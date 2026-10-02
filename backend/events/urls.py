from django.urls import path

from events.views import EventSearchView

app_name = "events"

urlpatterns = [
    path("search/", EventSearchView.as_view(), name="search"),
]
