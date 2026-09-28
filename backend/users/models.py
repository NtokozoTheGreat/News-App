from django.db import models
from django.contrib.auth.models import User
from datetime import date

# Create your models here.


class UserProfile(models.Model):

    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                related_name="profile")

    date_of_birth = models.DateField(blank=False, null=False)

    region = models.ForeignKey("content.Region",
                               on_delete=models.SET_NULL,
                               null=True,
                               related_name="users")

    image = models.ImageField(upload_to="upload/user_profile/",
                              blank=True, null=True)

    @property
    def age(self):
        today = date.today()

        age = today.year - self.date_of_birth.year

        if (today.month, today.day) < (self.date_of_birth.month,
                                       self.date_of_birth.day):

            age -= 1

        return age

    @property
    def diaplay_name(self):

        return f"{self.user.first_name} {self.user.last_name}"

    def __str__(self):
        return self.user.username
