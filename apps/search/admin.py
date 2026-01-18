"""Search history admin."""

from django.contrib import admin

from .models import SearchHistory


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    """SearchHistory admin."""

    list_display = ["query", "result_count", "search_time_ms", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["query"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]
