from django.conf import settings
from django.shortcuts import render


def reset_password_page(request):
    return render(
        request,
        "accounts/reset_password.html",
        {
            "reset_password_base_url": settings.RESET_PASSWORD_BASE_URL,
            "reset_password_api_base_url": settings.RESET_PASSWORD_API_BASE_URL,
        },
    )
