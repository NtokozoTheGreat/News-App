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

    def test_journalist_can_update_their_bio(self):
        journalist_profile = JournalistProfile.objects.create(
            user=self.user,
            bio="Original bio",
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("update_profile"),
            {
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "email": self.user.email,
                "date_of_birth": self.profile.date_of_birth.isoformat(),
                "region": self.profile.region.pk,
                "bio": "Updated journalist bio",
            },
        )

        self.assertEqual(response.status_code, 302)
        
        journalist_profile.refresh_from_db()
        self.assertEqual(journalist_profile.bio, "Updated journalist bio")
        
        
    def test_user_cannot_update_another_users_profile(self):

        other_user = User.objects.create_user(
            username="otheruser",
            password="OtherPassword123!",
            first_name="Other",
            last_name="Person",
            email="other@example.com",
        )

        other_profile = UserProfile.objects.create(
            user=other_user,
            date_of_birth="1998-05-15",
            region=self.profile.region,
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("update_profile"),
            {
                "username": "hackedusername",
                "first_name": "Hacked",
                "last_name": "User",
                "email": "hacked@example.com",
                "date_of_birth": "2000-01-01",
                "region": self.profile.region.pk,
            },
        )

        other_user.refresh_from_db()
        other_profile.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(other_user.username, "otheruser")
        self.assertEqual(other_user.first_name, "Other")
        self.assertEqual(other_user.email, "other@example.com")
        self.assertEqual(
            other_profile.date_of_birth.isoformat(),
            "1998-05-15",
        )


class DeleteProfileViewTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1",
            password="TestPassword123!",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            password="TestPassword123!",
        )

        self.journalist1 = JournalistProfile.objects.create(
            user=self.user1,
            bio="First journalist",
        )
        self.journalist2 = JournalistProfile.objects.create(
            user=self.user2,
            bio="Second journalist",
        )

    def test_user_can_delete_their_own_journalist_profile(self):
        self.client.login(
            username="user1",
            password="TestPassword123!",
        )

        response = self.client.post(reverse("delete_profile"))
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("update_profile"))
        self.assertFalse(
            JournalistProfile.objects.filter(user=self.user1).exists()
        )
        self.assertTrue(
            JournalistProfile.objects.filter(user=self.user2).exists()
        )
        
    def test_get_request_displays_confirmation_without_deleting_profile(self):
        self.client.login(
            username="user1",
            password="TestPassword123!",
        )

        response = self.client.get(reverse("delete_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "delete_profile.html")

        self.assertTrue(
            JournalistProfile.objects.filter(user=self.user1).exists()
        )
    
    def test_unauthenticated_user_is_redirected_to_login(self):
        response = self.client.get(reverse("delete_profile"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

        self.assertTrue(
            JournalistProfile.objects.filter(user=self.user1).exists()
        )

    def test_user_without_journalist_profile_is_redirected(self):
        self.client.login(
            username="user2",
            password="TestPassword123!",
        )

        self.journalist2.delete()

        response = self.client.get(reverse("delete_profile"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("update_profile"))

        self.assertTrue(
            JournalistProfile.objects.filter(user=self.user1).exists()
        )

    def test_unauthenticated_user_cannot_update_profile(self):
        response = self.client.post(
            reverse("update_profile"),
            {
                "username": "hackedusername",
                "first_name": "Hacked",
                "last_name": "User",
                "email": "hacked@example.com",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "profileuser")

class BecomeJournalistViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="regularuser",
            password="TestPassword123!",
        )

    def test_get_request_displays_page_without_creating_profile(self):
        self.client.login(
            username="regularuser",
            password="TestPassword123!",
        )

        response = self.client.get(reverse("become_journalist"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "become_journalist.html")

        self.assertFalse(
            JournalistProfile.objects.filter(user=self.user).exists()
        )
    
    def test_user_can_become_a_journalist(self):
        self.client.login(
            username="regularuser",
            password="TestPassword123!",
        )

        response = self.client.post(reverse("become_journalist"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("update_profile"))

        self.assertTrue(
            JournalistProfile.objects.filter(user=self.user).exists()
        )

    def test_user_with_existing_journalist_profile_cannot_create_another(self):
        JournalistProfile.objects.create(
            user=self.user,
            bio="Existing journalist",
        )

        self.client.login(
            username="regularuser",
            password="TestPassword123!",
        )

        response = self.client.post(reverse("become_journalist"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

        self.assertEqual(
            JournalistProfile.objects.filter(user=self.user).count(),
            1,
        )
        
    def test_unauthenticated_user_cannot_become_journalist(self):
        response = self.client.post(reverse("become_journalist"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

        self.assertEqual(
            JournalistProfile.objects.count(),
            0,
        )