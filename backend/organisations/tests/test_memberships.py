from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from organisations.models import Publisher, PublisherMembership, MembershipRequest
from users.models import JournalistProfile

# Create your tests here.


class PublisherMembersTests(TestCase):
    
    def setUp(self):
        
        self.admin_user = User.objects.create_user(
            username="publisher_admin",
            password="testpassword123"
        )
        
        self.admin_profile = JournalistProfile.objects.create(
            user=self.admin_user
        )
        
        self.publisher = Publisher.objects.create(name="Daily News")
        
        self.admin_membership = PublisherMembership.objects.create(
            journalist=self.admin_profile,
            publisher=self.publisher,
            role="admin",
            status="active"
        )

        pending_user = User.objects.create_user(
            username="pending_journalist",
            password="testpassword123"
        )

        pending_profile = JournalistProfile.objects.create(
            user=pending_user
        )

        self.pending_membership = PublisherMembership.objects.create(
            journalist=pending_profile,
            publisher=self.publisher,
            role="journalist",
            status="pending"
        )
        
        inactive_user = User.objects.create_user(
            username="inactive_journalist",
            password="testpassword123"
        )

        inactive_profile = JournalistProfile.objects.create(
            user=inactive_user
        )

        self.inactive_membership = PublisherMembership.objects.create(
            journalist=inactive_profile,
            publisher=self.publisher,
            role="journalist",
            status="inactive"
        )
        
        rejected_user = User.objects.create_user(
            username="rejected_journalist",
            password="testpassword123"
        )

        rejected_profile = JournalistProfile.objects.create(
            user=rejected_user
        )

        self.pending_membership = PublisherMembership.objects.create(
            journalist=rejected_profile,
            publisher=self.publisher,
            role="journalist",
            status="rejected"
        )
        
        leave_user = User.objects.create_user(
            username="leaving_journalist",
            password="testpassword123"
        )

        leave_profile = JournalistProfile.objects.create(user=leave_user)

        self.leave_membership = PublisherMembership.objects.create(
            journalist=leave_profile,
            publisher=self.publisher,
            role="journalist",
            status="active"
        )

        MembershipRequest.objects.create(
            membership=self.leave_membership,
            journalist=self.leave_membership.journalist,
            publisher=self.publisher,
            request_type="leave",
            status="pending"
        )

        self.url = reverse("organisations:publisher_members",
                           kwargs={"pk": self.publisher.pk})
        
    def test_active_admin_can_access_members_page(self):
        
        self.client.login(
            username="publisher_admin",
            password="testpassword123"
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["publisher"], self.publisher)
        
    def test_non_admin_cannot_access_members_page(self):
        
        user = User.objects.create_user(
            username="journalist",
            password="testpassword123"
        )
        
        profile = JournalistProfile.objects.create(user=user)
        
        PublisherMembership.objects.create(
            journalist=profile,
            publisher=self.publisher,
            role="journalist",
            status="active"
        )
        
        self.client.login(
            username="journalist",
            password="testpassword123"
        )
        
        response = self.client.get(self.url)
        
        self.assertRedirects(response, reverse(
            "organisations:publisher_detail", kwargs={"pk": self.publisher.pk}
        ))
        
    def test_user_without_journalist_profile_cannot_access_members_page(self):
        
        user = User.objects.create_user(
          username="ordinary_user",
            password="testpassword123"  
        )
        
        self.client.login(
            username="ordinary_user",
            password="testpassword123"
        )
        
        response = self.client.get(self.url)
        
        self.assertRedirects(response, reverse(
            "organisations:publisher_detail",
            kwargs={"pk": self.publisher.pk}
        ))
        
    def test_membership_counts_are_correct(self):
        
        self.client.login(
            username="publisher_admin",
            password="testpassword123" 
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.context["active_count"], 2)
        self.assertEqual(response.context["pending_count"], 1)
        self.assertEqual(response.context["inactive_count"], 1)
        self.assertEqual(response.context["rejected_count"], 1)
        self.assertEqual(response.context["pending_leave_count"], 1)
        self.assertEqual(response.context["total_count"], 5)
        
    def test_invalid_status_filter_defaults_to_active(self):
        
        self.client.login(
            username="publisher_admin",
            password="testpassword123"
        )
        
        response = self.client.get(self.url, {"status": "invalid"})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["membership_status"], "active")
        self.assertEqual(response.context["memberships"].count(), 2)