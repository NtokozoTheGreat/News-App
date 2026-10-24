from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .models import UserProfile, JournalistProfile
from content.models import Region
from datetime import date
# Create your tests here.

class HomeViewTests(TestCase):

    def test_home_page_returns_200(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")


class RegistrationViewTests(TestCase):

    def test_registration_page_returns_200(self):
        response = self.client.get(reverse("registration"))

        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_cannot_register_again(self):
        user = User.objects.create_user(
            username="existinguser",
            password="TestPassword123!"
        )

        self.client.force_login(user)

        response = self.client.get(reverse("registration"))

        self.assertRedirects(response, reverse("home"))

    def test_registration_page_does_not_create_user_on_get(self):
        self.client.get(reverse("registration"))

        self.assertEqual(User.objects.count(), 0)
        
    
    def setUp(self):
        self.region = Region.objects.create(
            name="Test Region"
        )

    def valid_registration_data(self):
        return {
            "username": "newuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "newuser@example.com",
            "date_of_birth": "2000-05-15",
            "region": str(self.region.pk),
            "password1": "SafeTestPassword!729",
            "password2": "SafeTestPassword!729",
        }

    def test_valid_registration_creates_user_and_profile(self):
        response = self.client.post(
            reverse("registration"),
            data=self.valid_registration_data(),
        )

        self.assertRedirects(response, reverse("home"))

        user = User.objects.get(username="newuser")

        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(
            UserProfile.objects.filter(
                user=user,
                date_of_birth="2000-05-15",
                region=self.region,
            ).exists()
        )

    def test_invalid_registration_does_not_create_user(self):
        data = self.valid_registration_data()
        data["password2"] = "DifferentPassword!729"

        response = self.client.post(
            reverse("registration"),
            data=data,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)
        self.assertContains(response, "form")


class UpdateProfileViewTests(TestCase):

    def setUp(self):
        self.region = Region.objects.create(
            name="Test Region"
        )

        self.user = User.objects.create_user(
            username="profileuser",
            password="SafeTestPassword!729",
            first_name="Test",
            last_name="User",
            email="profileuser@example.com",
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            date_of_birth=date(2000, 5, 15),
            region=self.region,
        )

    def test_unauthenticated_user_is_redirected_to_login(self):
        response = self.client.get(
            reverse("update_profile")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_authenticated_user_can_view_own_profile(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("update_profile")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "update_profile.html",
        )
        self.assertIsNotNone(response.context["user_form"])
        self.assertIsNotNone(response.context["profile_form"])
        self.assertIsNone(response.context["journalist_form"])

    def test_user_can_update_their_profile_details(self):
        self.client.force_login(self.user)

        updated_data = {
            "username": "updateduser",
            "first_name": "Updated",
            "last_name": "Person",
            "email": "updated@example.com",
            "date_of_birth": "1999-08-20",
            "region": str(self.region.pk),
        }

        response = self.client.post(
            reverse("update_profile"),
            data=updated_data,
        )

        self.assertRedirects(
            response,
            reverse("update_profile"),
        )

        self.user.refresh_from_db()
        self.profile.refresh_from_db()

        self.assertEqual(self.user.username, "updateduser")
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Person")
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertEqual(
            self.profile.date_of_birth,
            date(1999, 8, 20),
        )

