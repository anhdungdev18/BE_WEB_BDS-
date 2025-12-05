# accounts/utils/vietqr.py
import urllib.parse
from django.conf import settings


def build_vietqr_url(amount_vnd: int, transfer_note: str) -> str:
    """
    Trả về URL ảnh QR VietQR.
    Quét bằng app ngân hàng sẽ hiện sẵn STK + số tiền + nội dung.
    """
    base = (
        f"https://img.vietqr.io/image/"
        f"{settings.VIETQR_BANK_ID}-{settings.VIETQR_ACCOUNT_NO}-{settings.VIETQR_TEMPLATE}.png"
    )

    params = {
        "amount": amount_vnd,
        "addInfo": transfer_note,
        "accountName": settings.VIETQR_ACCOUNT_NAME,
    }

    return f"{base}?{urllib.parse.urlencode(params, safe='')}"
