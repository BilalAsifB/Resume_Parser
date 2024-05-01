from django.contrib import admin
from .models import UploadedResume
# Register your models here.

admin.site.register(UploadedResume)


class UploadedResumeAdmin(admin.ModelAdmin):
    list_display = ['candidate_name', 'get_resume_link']

    def get_resume_link(self, obj):
        return obj.resume.url

    get_resume_link.short_description = 'Resume'