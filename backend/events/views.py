from django.http import HttpRequest, JsonResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from events.models import EventFormat
from events.serializers import (
    EventCreatedSerializer,
    EventCreateSerializer,
    EventResultSerializer,
    EventSearchQuerySerializer,
    EventSearchResponseSerializer,
)
from events.services.geocoding import FixtureGeocodingService, GeocodingError
from events.services.search import EventSearchService


def health_check(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


class EventCreateView(APIView):
    @extend_schema(
        summary="Submit a community networking event",
        request=EventCreateSerializer,
        responses={201: EventCreatedSerializer},
    )
    def post(self, request) -> Response:
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        return Response(
            EventCreatedSerializer(event).data,
            status=status.HTTP_201_CREATED,
        )


class EventSearchView(APIView):
    @extend_schema(
        summary="Find and rank upcoming networking events",
        parameters=[
            OpenApiParameter("career", str, required=True),
            OpenApiParameter("location", str, required=True),
            OpenApiParameter("radius_miles", float, default=50),
            OpenApiParameter("start_date", str, required=False),
            OpenApiParameter("end_date", str, required=False),
            OpenApiParameter(
                "formats",
                str,
                many=True,
                required=False,
                enum=EventFormat.values,
            ),
        ],
        responses={200: EventSearchResponseSerializer},
    )
    def get(self, request) -> Response:
        serializer = EventSearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        try:
            results = EventSearchService(FixtureGeocodingService()).search(
                **serializer.validated_data
            )
        except GeocodingError as exc:
            return Response(
                {"location": [str(exc)]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "count": len(results),
                "events": EventResultSerializer(results, many=True).data,
            }
        )
