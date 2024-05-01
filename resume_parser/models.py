from django.db import models

# Create your models here.

class UploadedResume(models.Model):
    candidate_name = models.CharField(max_length=100)
    resume = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.candidate_name