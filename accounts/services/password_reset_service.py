import secrets, hashlib
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from accounts.models.password_reset_token import PasswordResetToken


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_password_reset_token_for_email(
    email: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    expiry_minutes: int = 30,
) -> None:
    """
    Luôn trả về None (không lộ email có tồn tại hay không).
    Nếu email tồn tại -> tạo token + gửi mail.
    """
    User = get_user_model()
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)

    PasswordResetToken.objects.create(
        user=user,
        token_hash=token_hash,
        expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
        ip_address=ip_address,
        user_agent=(user_agent or "")[:255] if user_agent else None,
    )

    fe_base = getattr(settings, "RESET_PASSWORD_BASE_URL", None) or getattr(
        settings, "FRONTEND_BASE_URL", "http://localhost:3000"
    )
    reset_link = f"{fe_base}/reset-password?token={raw_token}"

    subject = "Đặt lại mật khẩu"
    message = (
        f"Chào {getattr(user, 'username', 'bạn')},\n\n"
        f"Bạn vừa yêu cầu đặt lại mật khẩu. Nhấn link dưới đây để đặt lại mật khẩu (hết hạn sau {expiry_minutes} phút):\n"
        f"{reset_link}\n\n"
        f"Nếu bạn không yêu cầu, hãy bỏ qua email này."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[user.email],
        fail_silently=True,  # để không lộ thông tin & tránh crash khi dev chưa config mail
    )


def reset_password_with_token(raw_token: str, new_password: str) -> None:
    """
    Verify token -> đổi password -> mark used.
    Raise ValueError / ValidationError nếu token sai/hết hạn/mật khẩu yếu.
    """
    if not raw_token:
        raise ValueError("TOKEN_MISSING")

    token_hash = _hash_token(raw_token)
    prt = (
        PasswordResetToken.objects.select_related("user")
        .filter(token_hash=token_hash, used_at__isnull=True, expires_at__gt=timezone.now())
        .first()
    )
    if not prt:
        raise ValueError("TOKEN_INVALID_OR_EXPIRED")

    # Validate password theo Django validators (mạnh/yếu)
    validate_password(new_password, user=prt.user)

    # Đổi mật khẩu
    user = prt.user
    user.set_password(new_password)
    user.save(update_fields=["password"])

    # Mark token đã dùng
    prt.used_at = timezone.now()
    prt.save(update_fields=["used_at"])

    # (Tuỳ chọn) Revoke refresh token cũ nếu huynh dùng SimpleJWT blacklist
    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

        for t in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=t)
    except Exception:
        # Nếu project không bật blacklist app hoặc chưa migrate blacklist, bỏ qua
        pass
