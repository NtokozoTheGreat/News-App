from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from organisations.models import Publisher, PublisherMembership
from users.models import JournalistProfile

# Create your tests here.


class PublisherRegistrationTests(TestCase):
    
    def setUp(self):
        
        self.user = User.objects.create_user(
            username="journalist1",
            password="testpassword123"
        )
        
        self.journalist_profile = JournalistProfile.objects.create(user=self.user)
        
        self.url = reverse("organisations:register_publisher")
        
    def test_registration_page_loads_for_authenticated_user(self):
        
        self.client.login(
            username="journalist1",
            password="testpassword123"
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        
    def text_journalist_can_register_publisher(self):

        self.client.login(
            username="journalist1",
            password="testpassword123"
        )
        
        response = self.client.post(self.url, {
            "name": "Daily News",
            "description": "Independent news organisation",
            "email": "news@example.com",
            "phone_number": "1234567890",
            "website": "https://example.com"
        })
        
        self.assertEqual(Publisher.objects.count(), 1)
        
        publisher = Publisher.objects.get(name="Daily News")
        
        self.assertEqual(publisher.verification_status, "unverified")
        
        membership = PublisherMembership.onjects.get(
            journalist=self.journalist_profile,
            publisher=publisher
        )
        
        self.assertEqual(membership.role, "admin")
        self.assertEqual(membership.status, "activea")
        
        self.assertRedirects(response, reverse(
            "organisations:publisher_detail", kwargs={"pk": publisher.pk}
        ))
        
    def test_user_without_journalist_cannot_register(self):
    
        user_without_profile = User.objects.create_user(
            username="ordinaryuser",
            password="testpassword123"
        )
        
        self.client.login(
            username="ordinaryuser",
            password="testpassword123"
        )
        
        response = self.client.post(self.url, {
            "name": "Another News"
        })
        
        self.assertEqual(Publisher.objects.count(),0)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertFalse(response.context["form"].is_valid())


class PublisherListTests(TestCase):
    
    def setUp(self):
        
        self.publisher_a = Publisher.objects.create(name="City News")
        self.publisher_b = Publisher.objects.create(name="African Daily")
        self.publisher_c = Publisher.objects.create(name="Global Times")
        
        self.url = reverse("organisations:publisher_list")
        
    def test_publisher_list_page_loads(self):
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
    def tests_all_publishers_are_displayed(self):
        
        response = self.client.get(self.url)
        
        self.assertQuerySetEqual(
            response.context["publishers"],
            Publisher.objects.all().order_by("name")
        )
        
        self.assertEqual(len(response.context["publishers"]), 3)
        
    def test_publishers_are_ordered_alphabetically(self):
        
        response = self.client.get(self.url)
        
        publishers = list(response.context["publishers"])
        
        self.assertEqual(
            [publisher.name for publisher in publishers],
            ["African Daily", "City News", "Global Times"]
        )


class PublisherDetailTests(TestCase):
    
    def setUp(self):
        
        self.publisher = Publisher.objects.create(
            name="Daily News",
            description="An independent news organisation.",
            email="news@exmaple.com",
            phone_number="1234567890",
            website = "https://example.com"
        )
        
        self.url = reverse("organisations:publisher_detail",
                           kwargs={"pk": self.publisher.pk})
        
    def test_publisher_detail_page_loads(self):
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
    def test_correct_publisher_is_displayed(self):
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.context["publisher"], self.publisher)
        
    def test_nonexistent_publisher_returns_404(self):
        
        response = self.client.get(reverse("organisations:publisher_detail",
                                           kwargs={"pk": 9999}))
        self.assertEqual(response.status_code, 404)
        

class PublisherUpdateTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="publisher_admin",
            password="testpassword123"
        )
        
        self.journalist_profile = JournalistProfile.objects.create(user=self.user)
        
        self.publisher = Publisher.objects.create(
            name="Daily News",
            description="original description",
            email="news@example.com"
        )
        
        self.membership = PublisherMembership.objects.create(
            journalist=self.journalist_profile,
            publisher=self.publisher,
            role="admin",
            status="active"
        )
        
        self.url = reverse("organisations:update_publisher",
                           kwargs={"pk": self.publisher.pk})
        
    def test_active_admin_can_access_update_page(self):
        
        self.assertTrue(
            self.publisher.memberships.filter(
                journalist=self.journalist_profile,
                role="admin",
                status="active"
            ).exists()
        )
        
        self.client.login(
            username="publisher_admin",
            password="testpassword123"
        )
        
        self.assertTrue(self.client.session.get("_auth_user_id"))
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        
    def test_active_admin_can_update_publisher_details(self):
        
        self.client.login(
            username="publisher_admin",
            password="testpassword123"
        )
        
        self.assertTrue(self.client.session.get("_auth_user_id"))
        
        response = self.client.post(self.url, {
            "name": "Updated Daily News",
            "description": "Updated description",
            "email": "updated@example.com",
            "phone_number": "0123456789",
            "website": "https://example.com"
        })

        print("Response status:", response.status_code)
        print("Response URL:", getattr(response, "url", "No redirect"))
        print("Form errors:", response.context["form"].errors if response.context and "form" in response.context else "No form in response")
        
        self.publisher.refresh_from_db()
        
        self.assertEqual(self.publisher.name, "Updated Daily News")
        self.assertEqual(self.publisher.description, "Updated description")
        self.assertRedirects(response, (reverse(
            "organisations:publisher_detail",
            kwargs={"pk": self.publisher.pk}
        )))
        
    def test_non_adminjournalist_cannot_update_publisher(self):
        
        journalist_user = User.objects.create_user(
            username="ordinary_journalist",
            password="testpassword123"
        )
        
        journalist_profile = JournalistProfile.objects.create(user=journalist_user)
        
        PublisherMembership.objects.create(
            journalist=journalist_profile,
            publisher=self.publisher,
            role="journalist",
            status="active"
        )
        
        self.client.login(
            username="ordinary_journalist",
            password="testpassword123"
        )
        
        response = self.client.post(self.url, {"name": "Unauthorised Change"})
        
        self.publisher.refresh_from_db()
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.publisher.name, "Daily News")
 
    def test_user_without_journalist_profile_cannot_update_publisher(self):
        
        ordinary_user = User.objects.create_user(
            username="ordinary_user",
            password="testpassword123"
        )
        
        self.client.login(
            username="ordinary_user",
            password="testpassword123"
        )
        
        response = self.client.post(self.url, {
            "name": "Unauthorised Change"
        })
        
        self.publisher.refresh_from_db
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.publisher.name, "Daily News")