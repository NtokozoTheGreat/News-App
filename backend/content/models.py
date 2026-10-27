from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify

# Create your models here.


def generate_unique_slug(instance, value):
    """
    Generate a unique slug for a model instance.

    Example:
    breaking-news
    breaking-news-2
    breaking-news-3
    """

    base_slug = slugify(value)
    slug = base_slug
    counter = 2

    model_class = instance.__class__

    while model_class.objects.filter(
        slug=slug
    ).exclude(
        pk=instance.pk
    ).exists():

        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


def set_publishing_role_snapshot(instance):
    """
    Store the journalist's publisher role when the content
    is first associated with a publisher membership.

    The snapshot will not change after it has been set.
    """

    if (
        instance.publisher_membership
        and not instance.publishing_role_snapshot
    ):
        instance.publishing_role_snapshot = (
            instance.publisher_membership.role
        )


class Category(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                self,
                self.name
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "categories"


class Region(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                self,
                self.name
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(models.Model):

    IMAGE_COUNT_CHOICES = [
        (1, "1 Image"),
        (2, "2 Images"),
        (3, "3 Images"),
    ]

    LAYOUT_CHOICES = [
        ("a", "Layout A"),
        ("b", "Layout B"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("review", "Under Review"),
        ("approved", "Approved"),
        ("published", "Published"),
    ]

    title = models.CharField(
        max_length=255
    )

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    summary = models.TextField(
        blank=True
    )

    section_1 = models.TextField()

    section_2 = models.TextField(
        blank=True
    )

    image_count = models.PositiveSmallIntegerField(
        choices=IMAGE_COUNT_CHOICES,
        default=1
    )

    layout = models.CharField(
        max_length=1,
        choices=LAYOUT_CHOICES,
        default="a"
    )

    image_1 = models.ImageField(
        upload_to="uploads/articles/",
        blank=True,
        null=True
    )

    image_2 = models.ImageField(
        upload_to="uploads/articles/",
        blank=True,
        null=True
    )

    image_3 = models.ImageField(
        upload_to="uploads/articles/",
        blank=True,
        null=True
    )

    journalist = models.ForeignKey(
        "users.JournalistProfile",
        on_delete=models.SET_NULL,
        null=True,
        related_name="articles"
    )

    publisher_membership = models.ForeignKey(
        "organisations.PublisherMembership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles"
    )

    publishing_role_snapshot = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        editable=False
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="articles"
    )

    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        related_name="articles"
    )


    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

    reviewed_by = models.ForeignKey(
        "organisations.PublisherMembership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_articles"
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def clean(self):

        # Image validation

        if self.image_count >= 1 and not self.image_1:
            raise ValidationError(
                "This article requires at least one image."
            )

        if self.image_count >= 2 and not self.image_2:
            raise ValidationError(
                "You selected 2 or more images. "
                "Please upload image 2."
            )

        if self.image_count == 3 and not self.image_3:
            raise ValidationError(
                "You selected 3 images. "
                "Please upload image 3."
            )

        if self.image_count == 1 and (
            self.image_2 or self.image_3
        ):
            raise ValidationError(
                "You selected a 1-image layout."
            )

        if self.image_count == 2 and self.image_3:
            raise ValidationError(
                "You selected a 2-image layout."
            )

        # Publisher membership validation

        if (
            self.publisher_membership
            and self.publisher_membership.journalist
            != self.journalist
        ):
            raise ValidationError(
                "The selected publisher membership "
                "does not belong to this journalist."
            )

    @property
    def publisher(self):
        if self.publisher_membership:
            return self.publisher_membership.publisher

        return None

    @property
    def publishing_role(self):
        return self.publishing_role_snapshot

    @property
    def template_name(self):
        return (
            f"content/layouts/"
            f"{self.image_count}_image_{self.layout}.html"
        )


    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = generate_unique_slug(
                self,
                self.title
            )

        set_publishing_role_snapshot(self)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Newsletter(models.Model):

    title = models.CharField(
        max_length=200
    )

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    description = models.TextField()

    journalist = models.ForeignKey(
        "users.JournalistProfile",
        on_delete=models.SET_NULL,
        null=True,
        related_name="newsletters"
    )

    publisher_membership = models.ForeignKey(
        "organisations.PublisherMembership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletters"
    )

    publishing_role_snapshot = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        editable=False
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletters"
    )

    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletters"
    )

    image = models.ImageField(
        upload_to="uploads/newsletters/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def clean(self):

        if (
            self.publisher_membership
            and self.publisher_membership.journalist
            != self.journalist
        ):
            raise ValidationError(
                "The selected publisher membership "
                "does not belong to this journalist."
            )

    @property
    def publisher(self):
        if self.publisher_membership:
            return self.publisher_membership.publisher

        return None

    @property
    def publishing_role(self):
        return self.publishing_role_snapshot

    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = generate_unique_slug(
                self,
                self.title
            )

        set_publishing_role_snapshot(self)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ShortVideo(models.Model):

    title = models.CharField(
        max_length=200
    )

    video = models.FileField(
        upload_to="uploads/short_videos/"
    )

    description = models.TextField(
        blank=True
    )

    journalist = models.ForeignKey(
        "users.JournalistProfile",
        on_delete=models.SET_NULL,
        null=True,
        related_name="short_videos"
    )

    publisher_membership = models.ForeignKey(
        "organisations.PublisherMembership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="short_videos"
    )

    publishing_role_snapshot = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        editable=False
    )

    duration_seconds = models.PositiveIntegerField(
        editable=False,
        null=True,
        blank=True
    )

    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        related_name="short_videos"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="short_videos"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def clean(self):

        if (
            self.duration_seconds is not None
            and self.duration_seconds > 300
        ):
            raise ValidationError(
                "Short videos cannot be longer than 5 minutes."
            )

        if (
            self.publisher_membership
            and self.publisher_membership.journalist
            != self.journalist
        ):
            raise ValidationError(
                "The selected publisher membership "
                "does not belong to this journalist."
            )

    @property
    def publisher(self):
        if self.publisher_membership:
            return self.publisher_membership.publisher

        return None

    @property
    def publishing_role(self):
        return self.publishing_role_snapshot

    def save(self, *args, **kwargs):

        set_publishing_role_snapshot(self)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class LiveStream(models.Model):

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("live", "Live"),
        ("ended", "Ended"),
    ]

    title = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    journalist = models.ForeignKey(
        "users.JournalistProfile",
        on_delete=models.SET_NULL,
        null=True,
        related_name="live_streams"
    )

    publisher_membership = models.ForeignKey(
        "organisations.PublisherMembership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="live_streams"
    )

    publishing_role_snapshot = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        editable=False
    )

    stream_url = models.URLField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled"
    )

    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        related_name="live_streams"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="live_streams"
    )

    scheduled_for = models.DateTimeField(
        null=True,
        blank=True
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True
    )

    ended_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def clean(self):

        if (
            self.publisher_membership
            and self.publisher_membership.journalist
            != self.journalist
        ):
            raise ValidationError(
                "The selected publisher membership "
                "does not belong to this journalist."
            )

    @property
    def publisher(self):
        if self.publisher_membership:
            return self.publisher_membership.publisher

        return None

    @property
    def publishing_role(self):
        return self.publishing_role_snapshot

    def save(self, *args, **kwargs):

        set_publishing_role_snapshot(self)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title