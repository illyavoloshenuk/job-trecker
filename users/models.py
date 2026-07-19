from django.db import models

class UserProfile(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)

class JobApplication(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    date_applied = models.DateField(null=True, blank=True)
    job_link = models.URLField(blank=True)
    location = models.CharField(max_length=255,blank=True)
    salary = models.CharField(max_length=100,blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - {self.company}"
