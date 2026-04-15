import concurrent.futures
import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings as django_settings
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

logger = logging.getLogger(__name__)


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
        return "SMS service configure nahi. OTP sirf server log/terminal par hai — administrator se rabta karein."
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
            f"6 digit code isi email par bheja gaya hai: {email_addr} — "
            "usi inbox check karein (Spam / Promotions folder bhi dekhein). "
            "Brevo ka verified sender sirf 'From' hota hai; OTP recipient wohi hota hai jo form mein likha."
        )
    if email_key == "email_demo":
        return (
            "Demo — email OTP app/JSON mein (SMTP nahi set ya DEBUG + EMAIL_OTP_FALLBACK_ON_FAIL=1). "
            "Asli inbox ke liye Railway .env par Brevo SMTP + BREVO_SENDER_EMAIL set karein; production par DEBUG=0."
        )
    if email_key == "email_not_configured":
        return "Email SMTP configure nahi (.env mein BREVO_SMTP_LOGIN + BREVO_SMTP_KEY). Abhi sirf SMS code se aage badh sakte ho nahi — dono chahiye."
    return "Email par code nahi bheja ja saka. .env / Brevo SMTP check karein."


def _registration_email_fail_detail(code: str | None) -> str:
    """User-facing hint for email_failed (matches send_registration_email_otp error_code)."""
    c = (code or "unknown").strip()
    hints = {
        "from_header_missing": (
            "Server par 'From' email set nahi — Railway Variables mein BREVO_SENDER_EMAIL add karein "
            "(Brevo → Senders & IP → verified address, Gmail waghera). "
            "Agar SMTP login *@smtp-brevo.com hai to yeh field zaroori hai. "
            "Ya DEFAULT_FROM_EMAIL=AlyBank <verified@domain.com> set karein."
        ),
        "invalid_to": "Form mein valid email address likhein.",
        "smtp_auth": (
            "Brevo SMTP login/password galat — BREVO_SMTP_KEY (xsmtpsib-...) aur BREVO_SMTP_LOGIN "
            "(Brevo account email, kabhi-kabhi SMTP page par likha) dubara copy karein; space/quote na hon."
        ),
        "recipient_refused": (
            "SMTP ne recipient reject kiya — form wala email format / domain check karein; "
            "Brevo blocked-recipients list bhi dekhein."
        ),
        "smtp_disconnected": (
            "SMTP connection turant band — EMAIL_HOST/PORT (587+TLS ya 465+SSL), firewall, ya "
            "EMAIL_USE_SSL=1 + EMAIL_PORT=465 try karein agar 587 block ho."
        ),
        "smtp_data": (
            "Mail content / sender policy se reject — Brevo dashboard mein sender verify karein; "
            "From = verified sender hona chahiye."
        ),
        "smtp_server": (
            "Brevo server ne mail reject ki — Brevo Transactional logs / SMTP error code match karein; "
            "daily quota ya domain verification dekhein."
        ),
        "timeout": (
            "SMTP timeout — EMAIL_TIMEOUT barhao ya network check karein; Brevo smtp-relay.brevo.com reachable hai?"
        ),
        "network": (
            "Network / TLS issue — Railway se outbound 587 (ya 465) allow hai verify karein; "
            "EMAIL_USE_TLS / EMAIL_USE_SSL + PORT match karein."
        ),
        "unknown": (
            "SMTP error — server logs (Registration email OTP failed) mein exact exception dekhein; "
            "BREVO_SMTP_LOGIN, BREVO_SMTP_KEY, BREVO_SENDER_EMAIL, EMAIL_HOST=smtp-relay.brevo.com verify karein."
        ),
    }
    return hints.get(c, hints["unknown"])


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
                {
                    "detail": "Invalid username, email, or password.",
                    "errors": form.errors,
                },
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
                    "detail": "Valid email zaroori hai — OTP usi email ke inbox par jayega.",
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

        # Email + SMS in parallel — register request latency ≈ max(email, sms), not sum.
        _send_timeout = 45

        def _email_job():
            return send_registration_email_otp(email, email_otp)

        def _sms_job():
            return send_registration_otp(phone, sms_otp)

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                fut_email = pool.submit(_email_job)
                fut_sms = pool.submit(_sms_job)
                try:
                    _, email_key, email_otp_for_client, email_fail_code = (
                        fut_email.result(timeout=_send_timeout)
                    )
                except concurrent.futures.TimeoutError:
                    return Response(
                        {
                            "detail": "Email SMTP timeout — Brevo slow ya blocked. EMAIL_TIMEOUT / network check karein.",
                            "errors": {"email": ["Email send timed out."]},
                        },
                        status=status.HTTP_504_GATEWAY_TIMEOUT,
                    )
                try:
                    _, sms_key, otp_for_client, sms_twilio_code = fut_sms.result(
                        timeout=_send_timeout
                    )
                except concurrent.futures.TimeoutError:
                    return Response(
                        {
                            "detail": "SMS (Twilio) timeout — network ya Twilio check karein.",
                            "errors": {"phone": ["SMS send timed out."]},
                        },
                        status=status.HTTP_504_GATEWAY_TIMEOUT,
                    )
        except Exception:
            logger.exception("register/request parallel send failed")
            return Response(
                {"detail": "Verification codes could not be sent. Try again shortly."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if email_key == "email_failed":
            detail = _registration_email_fail_detail(email_fail_code)
            body: dict = {
                "detail": detail,
                "errors": {"email": ["Email delivery failed."]},
                "email_error": email_fail_code or "unknown",
            }
            if getattr(django_settings, "DEBUG", False):
                body["debug"] = (
                    "Django DEBUG=1 — agar OTP sirf test ke liye chahiye: EMAIL_OTP_FALLBACK_ON_FAIL=1 "
                    "(production par band rakhein)."
                )
            return Response(body, status=status.HTTP_400_BAD_REQUEST)
        if email_key == "email_not_configured":
            return Response(
                {
                    "detail": "Email OTP ke liye BREVO_SMTP_LOGIN + BREVO_SMTP_KEY aur BREVO_SENDER_EMAIL (agar login @smtp-brevo.com ho) set karein.",
                    "errors": {"email": ["Email (SMTP) not configured on server."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
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
            "email_otp_sent_to": email,
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
        if (
            not pending.email_otp_hash
            or _hash_otp(email_otp_raw) != pending.email_otp_hash
        ):
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
                {
                    "detail": "Phone number is missing or signup is invalid. Start again."
                },
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
