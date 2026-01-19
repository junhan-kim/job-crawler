from django.urls import path

from .views import LoadMoreView, SearchHistoryView, SearchView

urlpatterns = [
    path("search/", SearchView.as_view(), name="search"),
    path("search/history/", SearchHistoryView.as_view(), name="search-history"),
    path("search/more/", LoadMoreView.as_view(), name="search-more"),
]
