from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)


class JobApplication(models.Model):
    class Status(models.TextChoices):
        APPLIED = 'applied', 'Applied'
        INTERVIEW = 'interview', 'Interview'
        OFFER = 'offer', 'Offer'
        REJECTED = 'rejected', 'Rejected'
        CLOSED = 'closed', 'Closed'

    class LabelColor(models.TextChoices):
        NONE = 'none', 'No color'
        BLUE = 'blue', 'Blue'
        GREEN = 'green', 'Green'
        YELLOW = 'yellow', 'Yellow'
        PINK = 'pink', 'Pink'
        PURPLE = 'purple', 'Purple'
        GRAY = 'gray', 'Gray'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='job_applications',
        null=True,
        blank=True
    )

    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPLIED,
    )
    label_color = models.CharField(
        max_length=20,
        choices=LabelColor.choices,
        default=LabelColor.NONE,
    )
    date_applied = models.DateField(null=True, blank=True)
    job_link = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    salary = models.CharField(max_length=100, blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    is_favorite = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.company}"