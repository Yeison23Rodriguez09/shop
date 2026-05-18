from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import CustomUserCreationForm, UserBasicForm, UserProfileForm
from .models import CustomUser, UserProfile


class RegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = authenticate(
            self.request,
            username=form.cleaned_data.get('email'),
            password=form.cleaned_data.get('password1')
        )
        if user is not None:
            login(self.request, user)
        return response


class CustomLoginView(LoginView):
    template_name = 'users/login.html'

    def get_success_url(self):
        return reverse_lazy('core:home')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('core:home')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ensure profile exists
        UserProfile.objects.get_or_create(user=self.request.user)
        # Last 5 orders
        try:
            from apps.orders.models import Order
            context['recent_orders'] = Order.objects.filter(
                user=self.request.user
            ).order_by('-created_at')[:5]
        except Exception:
            context['recent_orders'] = []
        return context


class ProfileEditView(LoginRequiredMixin, View):
    template_name = 'users/profile_edit.html'

    def _get_profile(self, user):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile

    def get(self, request):
        user = request.user
        profile = self._get_profile(user)
        context = {
            'user_form': UserBasicForm(instance=user),
            'profile_form': UserProfileForm(instance=profile),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        profile = self._get_profile(user)
        user_form = UserBasicForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('users:profile')

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
        }
        return render(request, self.template_name, context)
