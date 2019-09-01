# users/urls.py
from django.urls import path
from .views import SignUpView, EditUserView

urlpatterns = [
    path('register/', SignUpView.as_view(), name='register'),
    path('edit/<int:id>', EditUserView, name='edituser'),
]