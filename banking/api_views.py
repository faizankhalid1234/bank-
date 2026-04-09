import hashlib
import secrets
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
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
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import AlyAuthForm, PaymentForm, RegisterForm
from .models import BankAccount, PendingSignup, Transaction, UserProfile
from .phone_utils import mask_phone, normalize_phone
from .services import ensure_bank_account, find_recipient, transfer
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
            "Demo mode — Twilio SMS set nahi hai. Neeche wala 6 digit code yahin se copy karke paste karein. "
            "Real SMS ke liye .env mein TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER bharo."
        )
    if sms_key == "sms_dev_console":
        return (
            "SMS service configure nahi. OTP sirf server log/terminal par hai — administrator se rabta karein."
        )
    if sms_key == "sms_trial_unverified":
        return (
            "Twilio trial restriction: jis number par OTP bhejni hai woh Twilio par verified nahi. "
            "Twilio Console mein recipient verify karein, ya account upgrade karein."
        )
    return "SMS nahi ja saki. Thori der baad dubara try karein ya Twilio keys check karein."


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
                "user": _user_payload(user),
                "account": _account_payload(ensure_bank_account(user)),
            }
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"ok": True})


class RegisterRequestView(APIView):
    """Validate details, create pending signup; SMS via Twilio, or demo OTP on screen when DEBUG."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        PendingSignup.objects.filter(expires_at__lt=timezone.now()).delete()
        fixed = (getattr(settings, "OTP_FIXED_PHONE_E164", None) or "").strip()
        payload = request.data
        if fixed:
            payload = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
            payload["phone"] = fixed
        np = normalize_phone(fixed if fixed else (request.data.get("phone") or ""))
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
        PendingSignup.objects.filter(username=username).delete()
        pwd_hash = make_password(cleaned["password1"])
        otp = _generate_otp()
        pending = PendingSignup.objects.create(
            username=username,
            email=(cleaned.get("email") or "").strip(),
            phone_number=phone,
            password_hash=pwd_hash,
            otp_hash=_hash_otp(otp),
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        _, sms_key, otp_for_client = send_registration_otp(phone, otp)
        masked = mask_phone(phone)
        payload = {
            "pending_id": str(pending.id),
            "expires_in": 600,
            "phone_masked": masked,
            "sms_sent": sms_key == "sms_sent",
            "sms_demo": sms_key == "sms_demo",
            "sms_dev_console": sms_key == "sms_dev_console",
            "sms_failed": sms_key == "sms_failed",
            "sms_trial_unverified": sms_key == "sms_trial_unverified",
            "message": _registration_otp_message(sms_key, masked),
        }
        if otp_for_client is not None:
            payload["otp"] = otp_for_client
        return Response(payload, status=status.HTTP_200_OK)


class RegisterConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        pending_id = request.data.get("pending_id")
        otp_raw = (request.data.get("otp") or "").strip().replace(" ", "")
        if not pending_id or not otp_raw:
            return Response(
                {"detail": "pending_id and otp are required."},
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
                {"detail": "Wrong verification code. Try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username__iexact=pending.username).exists():
            pending.delete()
            return Response(
                {"detail": "That username is no longer available. Start again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        email = (pending.email or "").strip()
        if email and User.objects.filter(email__iexact=email).exists():
            pending.delete()
            return Response(
                {"detail": "That email is already registered."},
                status=status.HTTP_400_BAD_REQUEST,
            )
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
