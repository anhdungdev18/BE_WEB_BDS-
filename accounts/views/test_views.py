from django.shortcuts import render

def logout_test_page(request):
    return render(request, "accounts/logout_test.html")
