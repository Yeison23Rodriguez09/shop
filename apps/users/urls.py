# beauty_shop\apps\users\urls.py
from django.urls import path
from .views import (
    RegisterView,
    CustomLoginView,
    CustomLogoutView,
    ProfileView,
    ProfileEditView
)

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/editar/', ProfileEditView.as_view(), name='profile_edit'),
]
