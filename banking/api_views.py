import hashlib
import secrets
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import AlyAuthForm, PaymentForm, RegisterForm
from .models import BankAccount, PendingSignup, Transaction, UserProfile
from .phone_utils import mask_phone, normalize_phone
from .services import ensure_bank_account, find_recipient, transfer
from .email_otp import send_registration_email_otp
from .sms import send_registration_otp


def _user_payload(user: User) -> dict:
    prof = UserProfile.objects.filter(user=user).first()
    return {
        "username": user.username,
        "first_name": user.first_name or "",
        "email": user.email or "",
        "phone": prof.phone if prof else "",
    }


def _registration_otp_message(sms_key: str, masked: str) -> str:
    if sms_key == "sms_sent":
        return f"Hum ne {masked} par 6 digit code bheja hai. Neeche likh dein."
    if sms_key == "sms_demo":
        return (
            "Local demo: Twilio SMS .env mein set nahi / SMS_OTP_FALLBACK_ON_TWILIO_FAIL=1 debug. "
            "Neeche wala code copy karke paste karein. Production SMS ke liye Twilio keys + paid/trial verified number zaroori."
        )
    if sms_key == "sms_dev_console":
        return (
            "SMS service configure nahi. OTP sirf server log/terminal par hai — administrator se rabta karein."
        )
    if sms_key == "sms_trial_unverified":
        return (
            "Twilio ne SMS reject ki (trial / verified number / permission). "
            "Console → Verified Caller IDs par yeh number verify karein, ya paid account, ya TWILIO_MESSAGING_SERVICE_SID use karein."
        )
    if sms_key == "sms_quota_exceeded":
        return (
            "Twilio daily SMS limit khatam (error 63038). Kal dubara try karein ya Twilio Console → Billing/Support se limit barhao. "
            "OTP user ke diye hue mobile number par hi jati hai — number galat nahi; account quota block kar raha hai."
        )
    if sms_key == "sms_failed":
        return (
            "SMS Twilio se nahi gayi (keys, From / Messaging Service, ya carrier). "
            "Server logs / sms_twilio_code dekhein, Twilio Debugger mein error match karein."
        )
    return "SMS nahi ja saki. Thori der baad dubara try karein ya Twilio keys check karein."


def _registration_email_otp_message(email_key: str, email_addr: str) -> str:
    if email_key == "email_sent":
        return (
            f"Email par 6 digit code bheja gaya: {email_addr} — Gmail / inbox check karein (Promotions/Spam bhi dekhein)."
        )
    if email_key == "email_demo":
        return (
            "Demo — email OTP neeche app mein dikhaya gaya (SMTP configure nahi ya DEBUG fallback)."
        )
    if email_key == "email_not_configured":
        return (
            "Email SMTP configure nahi (.env mein BREVO_SMTP_LOGIN + BREVO_SMTP_KEY). Abhi sirf SMS code se aage badh sakte ho nahi — dono chahiye."
        )
    return "Email par code nahi bheja ja saka. .env / Brevo SMTP check karein."


def _auth_token_for(user: User) -> str:
    token, _ = Token.objects.get_or_create(user=user)
    return token.key


def _account_payload(account: BankAccount) -> dict:
    return {
        "account_number": account.account_number,
        "iban": account.iban,
        "balance": str(account.balance),
    }


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def _generate_otp() -> str:
    return f"{secrets.randbelow(900000) + 100000:06d}"


def _tx_payload(tx: Transaction) -> dict:
    return {
        "id": tx.pk,
        "kind": tx.kind,
        "amount": str(tx.amount),
        "balance_after": str(tx.balance_after),
        "description": tx.description,
        "counterparty_account": tx.counterparty_account,
        "counterparty_iban": tx.counterparty_iban,
        "user_saved": tx.user_saved,
        "created_at": tx.created_at.isoformat(),
    }


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        form = AlyAuthForm(getattr(request, "_request", request), data=request.data)
        if not form.is_valid():
            return Response(
                {"detail": "Invalid username, email, or password.", "errors": form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = form.get_user()
        login(request, user)
        ensure_bank_account(user)
        return Response(
            {
                "token": _auth_token_for(user),
                "user": _user_payload(user),
                "account": _account_payload(ensure_bank_account(user)),
            }
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response({"ok": True})


class RegisterRequestView(APIView):
    """Validate details; send email OTP (Brevo SMTP) + SMS OTP; then save pending signup."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        PendingSignup.objects.filter(expires_at__lt=timezone.now()).delete()
        payload = request.data
        np = normalize_phone(request.data.get("phone") or "")
        if np:
            PendingSignup.objects.filter(phone_number=np).delete()
        form = RegisterForm(payload)
        if not form.is_valid():
            return Response(
                {"detail": "Registration failed.", "errors": form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cleaned = form.cleaned_data
        username = cleaned["username"]
        phone = cleaned["phone"]
        email = (cleaned.get("email") or "").strip()
        if not email:
            return Response(
                {
                    "detail": "Valid email zaroori hai — OTP Gmail/inbox par jayega.",
                    "errors": {"email": ["Enter a valid email address."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        PendingSignup.objects.filter(username=username).delete()
        PendingSignup.objects.filter(email__iexact=email).delete()
        pwd_hash = make_password(cleaned["password1"])
        sms_otp = _generate_otp()
        email_otp = _generate_otp()
        while email_otp == sms_otp:
            email_otp = _generate_otp()

        _, email_key, email_otp_for_client = send_registration_email_otp(email, email_otp)
        if email_key == "email_failed":
            return Response(
                {
                    "detail": "Email OTP nahi gaya. .env mein BREVO_SENDER_EMAIL = verified Gmail (Brevo Senders) + SMTP key check karein.",
                    "errors": {"email": ["Email delivery failed."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if email_key == "email_not_configured":
            return Response(
                {
                    "detail": "Email OTP ke liye BREVO_SMTP_LOGIN + BREVO_SMTP_KEY aur BREVO_SENDER_EMAIL (agar login @smtp-brevo.com ho) set karein.",
                    "errors": {"email": ["Email (SMTP) not configured on server."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        _, sms_key, otp_for_client, sms_twilio_code = send_registration_otp(phone, sms_otp)
        masked = mask_phone(phone)
        pending = PendingSignup.objects.create(
            username=username,
            email=email,
            phone_number=phone,
            password_hash=pwd_hash,
            otp_hash=_hash_otp(sms_otp),
            email_otp_hash=_hash_otp(email_otp),
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        payload = {
            "pending_id": str(pending.id),
            "expires_in": 600,
            "phone_masked": masked,
            "sms_to_fixed_verified": False,
            "sms_sent": sms_key == "sms_sent",
            "sms_demo": sms_key == "sms_demo",
            "sms_dev_console": sms_key == "sms_dev_console",
            "sms_failed": sms_key == "sms_failed",
            "sms_quota_exceeded": sms_key == "sms_quota_exceeded",
            "sms_trial_unverified": sms_key == "sms_trial_unverified",
            "message": _registration_otp_message(sms_key, masked),
            "email_sent": email_key == "email_sent",
            "email_demo": email_key == "email_demo",
            "email_message": _registration_email_otp_message(email_key, email),
        }
        if sms_twilio_code is not None:
            payload["sms_twilio_code"] = sms_twilio_code
        if otp_for_client is not None:
            payload["otp"] = otp_for_client
        if email_otp_for_client is not None:
            payload["email_otp"] = email_otp_for_client
        return Response(payload, status=status.HTTP_200_OK)


class RegisterConfirmView(APIView):
    """
    Creates the User only after both codes match: SMS (otp) and email (email_otp).
    No account exists in the database until this succeeds.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        pending_id = request.data.get("pending_id")
        otp_raw = (request.data.get("otp") or "").strip().replace(" ", "")
        email_otp_raw = (request.data.get("email_otp") or "").strip().replace(" ", "")
        if not pending_id or not otp_raw or not email_otp_raw:
            return Response(
                {"detail": "pending_id, otp (SMS), and email_otp are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            pending = PendingSignup.objects.get(pk=pending_id)
        except PendingSignup.DoesNotExist:
            return Response(
                {"detail": "Invalid or expired signup. Start registration again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if pending.expires_at < timezone.now():
            pending.delete()
            return Response(
                {"detail": "Verification code expired. Start registration again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if _hash_otp(otp_raw) != pending.otp_hash:
            return Response(
                {"detail": "Wrong SMS verification code. Try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not pending.email_otp_hash or _hash_otp(email_otp_raw) != pending.email_otp_hash:
            return Response(
                {"detail": "Wrong email verification code. Try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username__iexact=pending.username).exists():
            pending.delete()
            return Response(
                {"detail": "That username is no longer available. Start again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        email = (pending.email or "").strip()
        if not pending.phone_number:
            pending.delete()
            return Response(
                {"detail": "Phone number is missing or signup is invalid. Start again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            with transaction.atomic():
                user = User(username=pending.username, email=email)
                user.password = pending.password_hash
                user.save()
                UserProfile.objects.create(user=user, phone=pending.phone_number)
                account = ensure_bank_account(user)
                pending.delete()
        except IntegrityError:
            return Response(
                {"detail": "Could not create account. Try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        return Response(
            {
                "token": _auth_token_for(user),
                "user": _user_payload(user),
                "account": _account_payload(account),
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        account = ensure_bank_account(request.user)
        u = request.user
        return Response(
            {
                "user": _user_payload(u),
                "account": _account_payload(account),
            }
        )


class PaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        account = ensure_bank_account(request.user)
        form = PaymentForm(request.data)
        if not form.is_valid():
            return Response(
                {"detail": "Invalid payment.", "errors": form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        raw = form.cleaned_data["to_account_or_iban"]
        recipient = find_recipient(raw)
        if recipient is None:
            return Response(
                {"detail": "No AlyBank account found for that number or IBAN."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if recipient.pk == account.pk:
            return Response(
                {"detail": "You cannot send a payment to your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            out_tx, _ = transfer(
                account,
                recipient,
                form.cleaned_data["amount"],
                form.cleaned_data.get("description") or "",
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "message": "Payment sent.",
                "receipt_id": out_tx.pk,
                "transaction": _tx_payload(out_tx),
            }
        )


class ReceiptDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        account = ensure_bank_account(request.user)
        tx = get_object_or_404(
            Transaction,
            pk=pk,
            account=account,
            kind=Transaction.Kind.PAYMENT_SENT,
        )
        recipient = (
            BankAccount.objects.filter(account_number=tx.counterparty_account)
            .select_related("user")
            .first()
        )
        recipient_label = (
            (recipient.user.get_full_name() or recipient.user.username)
            if recipient
            else f"Account {tx.counterparty_account}"
        )
        return Response(
            {
                "transaction": _tx_payload(tx),
                "recipient_label": recipient_label,
                "account": _account_payload(account),
            }
        )


class SaveReceiptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        account = ensure_bank_account(request.user)
        tx = get_object_or_404(
            Transaction,
            pk=pk,
            account=account,
            kind=Transaction.Kind.PAYMENT_SENT,
        )
        tx.user_saved = True
        tx.save(update_fields=["user_saved"])
        return Response({"message": "Receipt saved to your list."})


class UnsaveReceiptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        account = ensure_bank_account(request.user)
        tx = get_object_or_404(
            Transaction,
            pk=pk,
            account=account,
            kind=Transaction.Kind.PAYMENT_SENT,
        )
        tx.user_saved = False
        tx.save(update_fields=["user_saved"])
        return Response({"message": "Removed from saved receipts."})


class HistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        account = ensure_bank_account(request.user)
        # Only this user's ledger — never mix other customers' rows
        qs = Transaction.objects.filter(account=account).order_by("-created_at", "-id")
        saved_only = request.GET.get("saved") == "1"
        if saved_only:
            qs = qs.filter(user_saved=True)
        return Response(
            {
                "transactions": [_tx_payload(t) for t in qs],
                "saved_only": saved_only,
                "account": _account_payload(account),
            }
        )


class BrandingView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "bank_name": "AlyBank",
                "bank_tagline": "Banking that feels effortless",
            }
        )
