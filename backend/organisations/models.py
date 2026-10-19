from django.db import models

# Create your models here.


class Publisher:

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

    journalist = models.ForeignKey("users.JournalistProfile", on_delete=models.CASCADE, related_name="publisher_memberships")

    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="memberships")

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    joined_at = models.DateTimeField(auto_now_add=True)

    def can_submit_articles(self):
        return self.role in [
            "journalist",
            "editor",
            "admin",
        ]

    def can_review_articles(self):
        return self.role in [
            "editor",
            "admin",
        ]

    def can_approve_articles(self):
        return self.role in [
            "editor",
            "admin",
        ]

    def can_manage_members(self):
        return self.role == "admin"

    def __str__(self):
        return (
            f"{self.journalist} - "
            f"{self.publisher} - "
            f"{self.role}"
        )