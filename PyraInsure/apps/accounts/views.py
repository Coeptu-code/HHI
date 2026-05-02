from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
def signup(request):
    next_url = request.GET.get("next") or request.POST.get("next") or "/"
    errors = {}

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm_password", "")

        if len(full_name) < 2:
            errors["full_name"] = "Please enter your full name."
        if not email or "@" not in email:
            errors["email"] = "Enter a valid email address."
        elif User.objects.filter(username=email).exists():
            errors["email"] = "An account with this email already exists."
        if len(password) < 8:
            errors["password"] = "Password must be at least 8 characters."
        if password != confirm:
            errors["confirm_password"] = "Passwords do not match."

        if not errors:
            name_parts = full_name.split(" ", 1)
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name_parts[0],
                last_name=name_parts[1] if len(name_parts) > 1 else "",
            )
            login(request, user)
            return redirect(next_url)

    return render(request, "registration/signup.html", {
        "errors": errors,
        "next": next_url,
        "values": request.POST,
    })
