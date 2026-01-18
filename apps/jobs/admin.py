from django.contrib import admin

from .models import JobPosting


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ["title", "company", "source", "location", "crawled_at", "is_active"]
    list_filter = ["source", "is_active", "crawled_at"]
    search_fields = ["title", "company", "description"]
    readonly_fields = ["crawled_at", "updated_at"]
