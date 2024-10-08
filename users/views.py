import random
import secrets
import string
from lib2to3.fixes.fix_input import context

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordResetView
from django.core.mail import send_mail
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from config.settings import EMAIL_HOST_USER
from users.forms import (PasswordForm, UserForm, UserProfileForm,
                         UserRegistrationForm)
from users.models import User


class RegisterView(CreateView):
    """
    контроллер регистрации пользователя
    """

    model = User
    form_class = UserRegistrationForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        user = form.save()
        user.is_active = False
        token = secrets.token_hex(16)
        user.token = token
        user.save()
        host = self.request.get_host()
        url = f"http://{host}/users/email-confirm/{token}"
        send_mail(
            subject="Подтверждение почты",
            message=f"Привет, перейти по ссылке для подтверждения почты? {url}",
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        return super().form_valid(form)


def email_verification(request, token):
    """
    верификация пользователя
    """
    user = get_object_or_404(User, token=token)
    user.is_active = True
    user.save()
    return redirect(reverse("users:login"))


class ProfileView(UpdateView):
    """
    контроллер редактирования профиля пользователя
    """

    model = User
    form_class = UserProfileForm
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user


class NewPasswordView(PasswordResetView):
    """
    контроллер сброса пароля пользователя
    """

    model = User
    form_class = PasswordForm
    template_name = "users/reset_password.html"
    success_url = reverse_lazy("users/login.html")

    def generate_password(self, length):
        characters = string.ascii_letters + string.digits + string.punctuation
        password = "".join(random.choice(characters) for _ in range(length))
        return password

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user = get_object_or_404(User, email=email)
        password = self.generate_password(16)
        user.set_password(password)
        user.save()
        send_mail(
            subject="вы запросили сброс пароля",
            message=f"новый пароль для входа: {password}",
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        return redirect(reverse("users:login"))


class UserUpdateView(UpdateView):
    model = User
    form_class = UserForm
    success_url = reverse_lazy("users:users_list")


class UserListView(LoginRequiredMixin, ListView):
    """
    контроллер для страницы отображения списка клиентов
    """

    model = User

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["users"] = User.objects.all()
        return context
