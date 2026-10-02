from django.urls import path

from events.views import EventCreateView, EventSearchView

app_name = "events"

urlpatterns = [
    path("", EventCreateView.as_view(), name="create"),
    path("search/", EventSearchView.as_view(), name="search"),
]
