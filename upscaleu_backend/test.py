from django.contrib.auth.models import User
from dashboard.models import UserProfile

user = User.objects.create_user(username="testsignal", password="1234")
profile = UserProfile.objects.get(user=user)
print(profile)
