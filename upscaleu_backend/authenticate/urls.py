from django.urls import path
from .views import RegisterAPIView, UserProfileAPIView, UpdateUserAPIView, ChangePasswordAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileAPIView.as_view(), name='user_profile'),
    path('profile/update/', UpdateUserAPIView.as_view(), name='update_user'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='change_password'),
]

