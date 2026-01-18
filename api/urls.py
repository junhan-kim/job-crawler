from django.urls import path

from .views import SearchHistoryView, SearchView

urlpatterns = [
    path("search/", SearchView.as_view(), name="search"),
    path("search/history/", SearchHistoryView.as_view(), name="search-history"),
]
