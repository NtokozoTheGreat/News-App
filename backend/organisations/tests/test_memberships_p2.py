from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from organisations.models import Publisher, PublisherMembership, MembershipRequest
from users.models import JournalistProfile
from unittest.mock import patch
from django.http import HttpResponse
# Create your tests here.


class ReviewLeaveRequestTests(TestCase):
    
    def setUp(self):
        
        self.admin_user = User.objects.create_user(
            username="admin",
            password="testpass123"
        )
        
        self.admin_profile = JournalistProfile.objects.create(user=self.admin_user)
        
        self.member_user = User.objects.create_user(
            username="member",
            password="testpass123"
        )
        
        self.member_profile = JournalistProfile.objects.create(user=self.member_user)
        
        self.publisher = Publisher.objects.create(name="Daily News") 
        
        self.admin_membership = PublisherMembership.objects.create(
            journalist=self.admin_profile,
            publisher=self.publisher,
            role="admin",
            status="active"
        )
        
        self.member_membership = PublisherMembership.objects.create(
            journalist=self.member_profile,
            publisher=self.publisher,
            role="journalist",
            status="active",
            pending_request="leave"
        )
        
        self.leave_request = MembershipRequest.objects.create(
            membership=self.member_membership,
            journalist=self.member_profile,
            publisher=self.publisher,
            request_type="leave",
            status="pending"
        )
        
        self.url = reverse("organisations:review_leave_request", 
                           kwargs={"pk": self.publisher.pk,
                                   "request_id": self.leave_request.pk})
        
        self.client.login(
            username="admin",
            password="testpass123"
        )
        
    def test_admin_can_approve_leave_request(self):
        
        response = self.client.post(self.url, {"decision": "approve"})
        
        self.member_membership.refresh_from_db()
        self.leave_request.refresh_from_db()
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.member_membership.status, "inactive")
        self.assertEqual(self.member_membership.pending_request, "")
        self.assertIsNotNone(self.leave_request.reviewed_at)
        
        self.assertEqual(self.leave_request.status, "approved")
        self.assertIsNotNone(self.leave_request.reviewed_at)
        self.assertEqual(self.leave_request.reviewed_by, self.admin_profile)
        
    def test_admin_can_reject_leave_request(self):
        
        response = self.client.post(self.url, {"decision": "reject"})
        
        self.member_membership.refresh_from_db()
        self.leave_request.refresh_from_db()
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.member_membership.status, "active")
        self.assertEqual(self.member_membership.pending_request, "")
        self.assertIsNone(self.member_membership.left_at)
        
        self.assertEqual(self.leave_request.status, "rejected")
        self.assertIsNotNone(self.leave_request.reviewed_at)
        self.assertEqual(self.leave_request.reviewed_by, self.admin_profile)