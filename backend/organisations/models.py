from django.db import models

# Create your models here.


class Publisher(models.Model):

    name = models.CharField(max_length=200, unique=True)

    description = models.TextField(blank=True)

    logo = models.ImageField(upload_to="uploads/publishers/", blank=True, null=True)

    email = models.EmailField(blank=True)

    phone_number = models.CharField(max_length=30, blank=True)

    website = models.URLField(blank=True)

    region = models.ForeignKey("content.Region", on_delete=models.SET_NULL, null=True, blank=True, related_name="publishers")

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PublisherMembership(models.Model):

    ROLE_CHOICES = [
        ("journalist", "Journalist"),
        ("editor", "Editor"),
        ("admin", "Publisher Admin"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending approval"),
        ("active", "Active"),
        ("rejected", "Rejected"),
    ]

    REQUEST_CHOICES = [
        ("join", "Join request"),
        ("leave", "Leave request"),
    ]

    journalist = models.ForeignKey("users.JournalistProfile", on_delete=models.CASCADE, related_name="publisher_memberships")

    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="memberships")

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    pending_request = models.CharField(max_length=20, choices=REQUEST_CHOICES, default="join")

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(
                fields=["journalist", "publisher"],
                name="unique_journalist_publisher_membership",
            )
        ]

    def can_submit_articles(self):
        return (self.staus == "active" and self.role in [
            "journalist",
            "editor",
            "admin",
        ]
        )

    def can_review_articles(self):
        return (self.staus == "active" and self.role in [
            "editor",
            "admin",
        ]
        )

    def can_approve_articles(self):
        return (self.staus == "active" and self.role in [
            "editor",
            "admin",
        ]
        )

    def can_manage_members(self):
        return (self.staus == "active" and self.role == "admin")

    def __str__(self):
        return (
            f"{self.journalist} - "
            f"{self.publisher} - "
            f"{self.role}"
        )


class MembershipRequest(models.Model):

    REQUEST_CHOICES = [
        ("join", "Join request"),
        ("leave", "leave request"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    memebership = models.ForeignKey(PublisherMembership, on_delete=models.CASCADE, related_name="requests")
    
    request_type = models.CharField(max_length=10, choices=REQUEST_CHOICES)

    requested_at = models.DateTimeField(auto_now_add=True)
    
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    reviewed_by = models.ForeignKey("users.JournalistProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_membership_requests",)

    class Meta:
        
        constraints = [models.UniqueConstraint(
            fields=["membership"],
            condition=Q(status="pending"),
            name="unique_pending_membership_request",
        )
        ]
        
        ordring = ["-requested_at"]
        
        def __str__(self):
        return (
            f"{self.request_type.title()} request: "
            f"{self.membership} ({self.status})"
        )