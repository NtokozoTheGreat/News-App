from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from organisations.models import Publisher, PublisherMembership, MembershipRequest
from users.models import JournalistProfile
from unittest.mock import patch
from django.http import HttpResponse
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
        

class RequestToJoin(TestCase):
    
    def setUp(self):
        
        self.user = User.objects.create_user(
            username="joining_journalist",
            password="testpassword123"
        )
        
        self.journalist_profile = JournalistProfile.objects.create(
            user=self.user
        )
        
        self.publisher = Publisher.objects.create(
            name="Daily News"
        )
        
        self.url = reverse("organisations:request_to_join",
                           kwargs={"pk": self.publisher.pk})
        
    def test_user_without_journalist_profile_cannot_request_to_join(self):
        
        user = User.objects.create_user(
            username="ordinary_user",
            password="testpassword123"
        )
        
        self.client.login(
            username="ordinary_user",
            password="testpassword123"
        )
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PublisherMembership.objects.filter(
                publisher=self.publisher
            ).exists()
        )
        
    def test_new_journalist_can_request_to_join(self):
        
        self.client.login(
            username="joining_journalist",
            password="testpassword123"
        )
        
        response = self.client.post(self.url)
        
        membership = PublisherMembership.objects.get(
            journalist=self.journalist_profile,
            publisher=self.publisher
        )
        
        self.assertEqual(membership.role, "journalist")
        self.assertEqual(membership.status, "pending")
        self.assertEqual(membership.pending_request, "join")
        
        self.assertTrue(MembershipRequest.objects.filter(
            membership=membership,
            request_type="join",
            status="pending"
            ).exists()
        )
        
        self.assertEqual(response.status_code, 302)
        
    def test_active_member_cannot_submit_another_join_request(self):
        
        PublisherMembership.objects.create(
           journalist=self.journalist_profile,
            publisher=self.publisher,
            role="journalist",
            status="active" 
        )
        
        self.client.login(
            username="joining_journalist",
            password="testpassword123"
        )
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MembershipRequest.objects.count(), 0)
        
    def test_existing_pending_request_is_not_duplicated(self):
        
        membership = PublisherMembership.objects.create(
            journalist=self.journalist_profile,
            publisher=self.publisher,
            role="journalist",
            status="pending"
        )
        
        MembershipRequest.objects.create(
            membership=membership,
            journalist=self.journalist_profile,
            publisher=self.publisher,
            request_type="join",
            status="pending"
        )
        
        self.client.login(
            username="joining_journalist",
            password="testpassword123"
        )
        
        response = self.client.post(self.url)
        
        print("STATUS:", response.status_code)
        print("REASON:", response.reason_phrase)
        print("HOST:", response.wsgi_request.get_host())
        print("LOCATION:", response.get("Location"))
                
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MembershipRequest.objects.count(), 1)
        
    def test_get_reuqest_is_not_allowed(self):
        
        self.client.login(
            username="joining_journalist",
            password="testpassword123"
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 405)


class PublisherMembershipRequestTests(TestCase):
    
    def setUp(self):
        
        self.admin_user = User.objects.create_user(
            username="publisher_admin",
            password="testpassword123"
        )
        
        self.admin_profile = JournalistProfile.objects.create(
            user=self.admin_user
        )
        
        self.publisher = Publisher.objects.create(name="Daily News")
        
        self.url = reverse("organisations:publisher_membership_requests",
                           kwargs={"pk": self.publisher.pk})
        
        PublisherMembership.objects.create(
            journalist=self.admin_profile,
            publisher=self.publisher,
            role="admin",
            status="active"
        )
        
        self.applicant_user = User.objects.create_user(
            username="applicant",
            password="testpassword123"
        )
        
        self.applicant_profile = JournalistProfile.objects.create(
            user=self.applicant_user
        )
        
        self.applicant_membership = PublisherMembership.objects.create(
            journalist=self.applicant_profile,
            publisher=self.publisher,
            role="journalist",
            status="pending"
        )
        
        self.join_request = MembershipRequest.objects.create(
            membership=self.applicant_membership,
            journalist=self.applicant_profile,
            publisher=self.publisher,
            request_type="join",
            status="pending"
        )
        
    def test_active_admin_can_access_membership_requests(self):
        
        self.client.login(
            username="publisher_admin",
            password="testpassword123"
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
    def test_non_admin_cannot_acccess_membership_requests(self):
        
        self.client.login(
            username="applicant",
            password="testpassword123"
        )
        
        response = self.client.get(self.url)
        
        self.assertRedirects(response, reverse("organisations:publisher_detail", 
                                               kwargs={"pk": self.publisher.pk}))
        
    def test_user_withou_journalist_profile_cannot_access_membership_request(self):
        
        user = User.objects.create_user(
            username="ordinary_user",
            password="testpassword123"
        )
        
        self.client.login(
            username="ordinary_user",
            password="testpassword123"
        )
        
        response = self.client.get(self.url)
        
        self.assertRedirects(response, reverse("organisations:publisher_detail",
                                               kwargs={"pk": self.publisher.pk}))

        
    def test_only_pending_join_requests_for_pubisher_are_displayed(self):
        
        self.client.login(
            username="publisher_admin",
            password="testpassword123"
        )
        
        response = self.client.get(self.url)
        
        self.assertQuerySetEqual(response.context["membership_requests"],
                                 [self.join_request])
        
        
    def test_publisher_is_in_context(self):
        
        self.client.login(
            username="publisher_admin",
            password="testpassword123"
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.context["publisher"], self.publisher)


class ReviewMembershipRequestTests(TestCase):

    def setUp(self):
        
        self.admin_user = User.objects.create_user(
            username="publisher_admin",
            password="testpassword123"
        )
        
        self.admin_profile = JournalistProfile.objects.create(
            user=self.admin_user
        )
        
        self.applicant_user = User.objects.create_user(
            username="applicant",
            password="testpassword123"
        )
        
        self.applicant_profile = JournalistProfile.objects.create(
            user=self.applicant_user
        )
        
        self.publisher = Publisher.objects.create(name="Daily News")

        self.admin_membership = PublisherMembership.objects.create(
            journalist=self.admin_profile,
            publisher=self.publisher,
            role="admin",
            status="active"
        )
        
        self.applicant_membership = PublisherMembership.objects.create(
            journalist=self.applicant_profile,
            publisher=self.publisher,
            role="journalist",
            status="pending",
            pending_request="join"
        )
        
        self.membership_request = MembershipRequest.objects.create(
            membership=self.applicant_membership,
            journalist=self.applicant_profile,
            publisher=self.publisher,
            request_type="join",
            status="pending"
        )
        
        self.url = reverse("organisations:review_membership_request",
                            kwargs={"pk": self.publisher.pk,
                                    "request_id": self.membership_request.pk})

        self.client.login(
            username="publisher_admin",
            password="testpassword123"
        )

    def test_active_admin_can_approve_membership_request(self):
        
        response = self.client.post(self.url, {"decision": "approve"})

        self.applicant_membership.refresh_from_db()
        self.membership_request.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.applicant_membership.status, "active")
        self.assertEqual(self.applicant_membership.role, "journalist")
        self.assertEqual(self.membership_request.status, "approved")
        self.assertIsNotNone(self.membership_request.reviewed_at)
        self.assertEqual(self.membership_request.reviewed_by,
                         self.admin_profile)

    def test_active_admin_can_reject_membership_request(self):
        response = self.client.post(self.url, {"decision": "reject"})
        
        self.applicant_membership.refresh_from_db()
        self.membership_request.refresh_from_db()
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.applicant_membership.status, "rejected")
        self.assertEqual(self.membership_request.status, "rejected")
        self.assertIsNotNone(self.membership_request.reviewed_at)
        self.assertEqual(self.membership_request.reviewed_by,
                         self.admin_profile)

    def test_non_admin_cannot_review_membership_request(self):
        
        self.client.logout()
        
        self.client.login(
            username="applicant",
            password="testpassword123"
        )
        
        response = self.client.post(self.url,{"decision": "approve"})

        self.applicant_membership.refresh_from_db()
        self.membership_request.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.applicant_membership.status, "pending")
        self.assertEqual(self.membership_request.status, "pending")

    def test_invalid_decision_does_not_change_membership(self):
        
        response = self.client.post(self.url, {"decision": "invalid"})

        self.applicant_membership.refresh_from_db()
        self.membership_request.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.applicant_membership.status, "pending")
        self.assertEqual(self.membership_request.status, "pending")

    def test_already_reviewed_request_cannot_be_reviewed_again(self):
        
        self.membership_request.status = "approved"
        self.membership_request.save()

        response = self.client.post(self.url, {"decision": "reject"})

        self.applicant_membership.refresh_from_db()
        self.membership_request.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.applicant_membership.status, "pending")
        self.assertEqual(self.membership_request.status, "approved")

    def test_get_request_is_not_allowed(self):
        
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_unrelated_journalist_cannot_review_membership_request(self):
        
        unrelated_user = User.objects.create_user(
            username="unrelated_journalist",
            password="testpassword123"
        )
        
        JournalistProfile.objects.create(user=unrelated_user)
        
        self.client.logout()
        
        self.client.login(
            username="unrelated_journalist",
            password="testpassword123"
        )

        response = self.client.post(self.url, {"decision": "approve"})
        
        self.applicant_membership.refresh_from_db()
        self.membership_request.refresh_from_db()
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.applicant_membership.status, "pending")
        self.assertEqual(self.membership_request.status, "pending")
    
    
class PromoteMemberTests(TestCase):
    
    def setUp(self):
        
        self.admin_user = User.objects.create_user(
            username="publisher_admin",
            password="testpassword123" 
        )
        
        self.admin_profile = JournalistProfile.objects.create(
            user=self.admin_user
        )
        
        self.member_user = User.objects.create_user(
            username="target_member",
            password="testpassword123"
        )
        
        self.member_profile = JournalistProfile.objects.create(
            user=self.member_user
        )
        
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
            status="active"
        )
        
        self.url = reverse("organisations:promote_member",
                           kwargs={"pk": self.publisher.pk,
                                   "membership_id": self.member_membership.pk}
                           )
        
        self.client.login(
            username="publisher_admin",
            password="testpassword123"
        )
        
    def test_active_admin_can_promote_member(self):
        
        response = self.client.post(self.url)
        
        self.member_membership.refresh_from_db()
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.member_membership.role, "admin")
        
    def test_non_admin_cannot_promote_member(self):
        
        self.client.logout()
        self.client.login(
            username="target_member",
            password="testpassword123"
        )
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.member_membership.role, "journalist")
        
    def test_user_without_journalist_profile_cannot_promote_member(self):
        
        user = User.objects.create_user(
            username="ordinary_user",
            password="testpassword123"
        )
        
        self.client.logout()
        self.client.login(
            username="ordinary_user",
            password="testpassword123"
        )
        
        response = self.client.post(self.url)
        
        self.member_membership.refresh_from_db()
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.member_membership.role, "journalist")
        
    def test_inactive_member_cannot_be_promoted(self):
        
        self.member_membership.status = "inactive"
        self.member_membership.save()
        
        response = self.client.post(self.url)
        
        self.member_membership.refresh_from_db()
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.member_membership.role, "journalist")
        
    def test_member_who_is_already_admin_is_not_promoted_again(self):
        
        self.member_membership.role = "admin"
        self.member_membership.save()
        
        response = self.client.post(self.url)
        
        self.member_membership.refresh_from_db()
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.member_membership.role, "admin")
        
    def test_member_with_pending_leave_request_cannot_be_promoted(self):
        
        MembershipRequest.objects.create(
            membership=self.member_membership,
            journalist=self.member_profile,
            publisher=self.publisher,
            request_type="leave",
            status="pending"
        )
        
        response = self.client.post(self.url)
        
        self.member_membership.refresh_from_db()
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.member_membership.role, "journalist")
        
    def test_get_request_is_not_allowed(self):
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 405)


class DemoteMemberTests(TestCase):
    
    def setUp(self):
        
        self.admin_user = User.objects.create_user(
            username="publisher_admin",
            password="testpassword123"
        )
        
        self.admin_profile = JournalistProfile.objects.create(
            user=self.admin_user
        )
        
        self.target_user = User.objects.create_user(
            username="target_admin",
            password="testpassword123"
        )
        
        self.target_profile = JournalistProfile.objects.create(
            user=self.target_user
        )
        
        self.member_user = User.objects.create_user(
            username="regular_member",
            password="testpassword123" 
        )
        
        self.member_profile = JournalistProfile.objects.create(
            user=self.member_user
        )
        
        self.publisher = Publisher.objects.create(name="Daily News")
        
        self.admin_membership = PublisherMembership.objects.create(
            journalist=self.admin_profile,
            publisher=self.publisher,
            role="admin",
            status="active"
        )
        
        self.target_admin_membership = PublisherMembership.objects.create(
            journalist=self.target_profile,
            publisher=self.publisher,
            role="admin",
            status="active"
        )
        
        self.member_membership = PublisherMembership.objects.create(
            journalist=self.member_profile,
            publisher=self.publisher,
            role="journalist",
            status="active"
        )
        
        self.url = reverse("organisations:demote_member",
                           kwargs={"pk": self.publisher.pk,
                                   "membership_id": self.target_admin_membership.pk})
        
        self.client.login(
            username="publisher_admin",
            password="testpassword123"
        )
        
    def test_active_admin_can_demote_another_admin(self):
        
        response = self.client.post(self.url, {"new_role": "journalist"})
        
        self.assertEqual(response.status_code, 302)
        
        self.target_admin_membership.refresh_from_db()
        self.assertEqual(self.target_admin_membership.role, "journalist")
        
    def test_non_admin_cannot_demote_member(self):
        
        self.client.login(
            username="regular_member",
            password="testpassword123"
        )
        
        response = self.client.post(self.url, {"new_role": "journalist"})
        
        self.assertEqual(response.status_code, 302)
        
        self.target_admin_membership.refresh_from_db()
        self.assertEqual(self.target_admin_membership.role, "admin")
        
    def test_user_without_journalist_profile_cannot_demote_member(self):
        
        user = User.objects.create_user(
            username="ordinary_user",
            password="testpassword123"
        )
        
        self.client.login(
            username="ordinary_user",
            password="testpassword123" 
        )
        
        response = self.client.post(self.url, {"new_role": "journalist"})
        
        self.assertEqual(response.status_code, 302)
        
        self.target_admin_membership.refresh_from_db()
        self.assertEqual(self.target_admin_membership.role, "admin")
        
    def test_non_admin_cannot_be_demoted(self):
        
        url = reverse("organisations:demote_member", kwargs={
            "pk": self.publisher.pk, "membership_id": self.member_membership.pk})
        
        response = self.client.post(url, {"new_role": "editor"})
        
        self.assertEqual(response.status_code, 302)
        
        self.member_membership.refresh_from_db()
        self.assertEqual(self.member_membership.role, "journalist")
        
    def test_last_active_cannot_be_demoted(self):
        
        self.target_admin_membership.status = "inactive"
        self.target_admin_membership.save(update_fields=["status"])
        
        urls = reverse("organisations:demote_member", kwargs={
            "pk": self.publisher.pk,
            "membership_id": self.admin_membership.pk
        })
        
        response = self.client.post(self.url, {"new_role": "journalist"})
        
        self.assertEqual(response.status_code, 302)
        
        self.admin_membership.refresh_from_db()
        self.assertEqual(self.admin_membership.role, "admin")
        
    def test_admin_with_pending_leave_request_cannot_be_demoted(self):
        
        MembershipRequest.objects.create(
            membership=self.target_admin_membership,
            journalist=self.target_profile,
            publisher=self.publisher,
            request_type="leave",
            status="pending"
        )
        
        response = self.client.post(self.url, {"new_role": "journalist"})
        
        self.assertEqual(response.status_code, 302)
        
        self.target_admin_membership.refresh_from_db()
        self.assertEqual(self.target_admin_membership.role, "admin")
        
    def test_invalid_role_is_rejected(self):
        
        response = self.client.post(self.url, {"new_role": "superuser"})
        
        self.assertEqual(response.status_code, 302)
        
        self.target_admin_membership.refresh_from_db()
        self.assertEqual(self.target_admin_membership.role, "admin")
        
    def test_get_request_is_not_allowed(self):
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 405)

   
class RequestToLeaveTests(TestCase):
    
    def setUp(self):
        
        self.user = User.objects.create_user(
            username="journalist",
            password="testpassword123"
        )
        
        self.journalist_profile = JournalistProfile.objects.create(
            user=self.user
        )
        
        self.publisher = Publisher.objects.create(name="Daily News")
        
        self.membership = PublisherMembership.objects.create(
            journalist=self.journalist_profile,
            publisher=self.publisher,
            role="journalist",
            status="active"
        )
        
        self.url = reverse("organisations:request_to_leave",
                           kwargs={"pk": self.publisher.pk})
        
        self.client.login(
            username="journalist",
            password="testpassword123" 
        )
        
    def test_active_member_can_request_to_leave(self):
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 302)
        
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.pending_request, "leave")
        
        leave_request = MembershipRequest.objects.get(
            membership=self.membership,
            request_type="leave",
            status="pending"
        )
        
        self.assertIsNotNone(leave_request)
        
    def test_user_without_journalist_profile_cannot_request_to_leave(self):
        
        user = User.objects.create_user(
            username="ordinary_user",
            password="testpassword123"
        )
        
        self.client.login(
            username="ordinary_user",
            password="testpassword123"
        )
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(MembershipRequest.objects.filter(
            publisher=self.publisher,
            request_type="leave"
        ).exists())
        
    def test_non_member_cannot_request_to_leave(self):
        
        self.membership.delete()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(MembershipRequest.objects.filter(
            publisher=self.publisher,
            request_type= "leave"
        ).exists())
        
    def test_inactive_member_cannot_request_to_leave(self):
        
        self.membership.status = "inactive"
        self.membership.save(update_fields=["status"])
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(MembershipRequest.objects.filter(
            membership=self.membership,
            request_type="leave"
        ).exists())
        
    def test_admin_cannot_request_to_leave_before_demotion(self):
        
        self.membership.role = "admin"
        self.membership.save(update_fields=["role"])
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(MembershipRequest.objects.filter(
            membership=self.membership,
            request_type="leave"
        ).exists())
    
    def test_member_with_pending_request_cannot_submit_another(self):
            
        MembershipRequest.objects.create(
            membership=self.membership,
            journalist=self.journalist_profile,
            publisher=self.publisher,
            request_type="join",
            status="pending"
        )
        
        response = self.client.post(self.url)
                
        self.assertEqual(response.status_code, 302)

        self.assertEqual(MembershipRequest.objects.filter(
            membership=self.membership, status="pending").count(), 1)

    def test_get_request_is_not_allowed(self):
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 405)


class PublisherLeaveRequestTests(TestCase):

    def setUp(self):
        
        self.admin_user = User.objects.create_user(
            username="publisher_admin",
            password="testpassword123"
        )
        
        self.admin_profile = JournalistProfile.objects.create(user=self.admin_user)
        
        self.publisher = Publisher.objects.create(name="DAily News")
        
        self.admin_membership = PublisherMembership.objects.create(
            journalist=self.admin_profile,
            publisher=self.publisher,
            role="admin",
            status="active"
        )
        
        self.member_user = User.objects.create_user(
            username="journalist",
            password="testpassword123"
        )
        
        self.member_profile = JournalistProfile.objects.create(
            user=self.member_user
        )
        
        self.member_membership = PublisherMembership.objects.create(
            journalist=self.member_profile,
            publisher=self.publisher,
            role="journalist",
            status="active"
        )
        
        self.url =reverse("organisations:publisher_leave_requests",
                          kwargs={"pk": self.publisher.pk})
        
        self.client.login(
            username="publisher_admin",
            password="testpassword123"
        )
        
    def test_publisher_admin_can_access_leave_requests(self):
        
        with patch("organisations.views.render", return_value=HttpResponse()
                   )as mock_render:
            
            response = self.client.get(self.url)
            
        self.assertEqual(response.status_code, 200)
        mock_render.assert_called_once()
        
        context = mock_render.call_args.args[2]
        
        self.assertEqual(context["publisher"], self.publisher)
        self.assertIn("leave_requests", context)
        
    def test_non_admin_cannot_access_leave_requests(self):
        
        self.client.login(
            username="journalist",
            password="testpassword123"
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(
            "organisations:publisher_detail", kwargs={"pk": self.publisher.pk}
        ))
        
    def test_uanthenticated_user_cannot_leave_requests(self):
        
        self.client.logout()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())
        
    def test_only_pending_leave_requests_are_included(self):
        
        leave_request = MembershipRequest.objects.create(
            membership=self.member_membership,
            journalist=self.member_profile,
            publisher=self.publisher,
            request_type="leave",
            status="pending"
        )
        
        MembershipRequest.objects.create(
            membership=self.admin_membership,
            journalist=self.admin_profile,
            publisher=self.publisher,
            request_type="join",
            status="pending"
        )
        
        MembershipRequest.objects.create(
            membership=self.admin_membership,
            journalist=self.admin_profile,
            publisher=self.publisher,
            request_type="leave",
            status="approved"
        )
        
        with patch("organisations.views.render", return_value=HttpResponse()
                   )as mock_render:
            
            self.client.get(self.url)
            
        context = mock_render.call_args.args[2]
        requests = list(context["leave_requests"])
        
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0], leave_request)
    
    def test_request_from_other_publishers_are_excluded(self):
        
        other_publisher = Publisher.objects.create(name="Other News")
        
        other_membership = PublisherMembership.objects.create(
            journalist=self.member_profile,
            publisher=other_publisher,
            role="journalist",
            status="active"
        )
    
        other_leave_request = MembershipRequest.objects.create(
            membership=other_membership,
            journalist=self.member_profile,
            publisher=other_publisher,
            request_type="leave",
            status="pending"
        )
        
        with patch("organisations.views.render", return_value=HttpResponse()
                   ) as mock_render:
            
            self.client.get(self.url)
            
            context = mock_render.call_args.args[2]
            requests = list(context["leave_requests"])
            
            self.assertNotIn(other_leave_request, requests)
            
