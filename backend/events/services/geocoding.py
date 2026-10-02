from abc import ABC, abstractmethod

from django.contrib.gis.geos import Point


class GeocodingError(ValueError):
    pass


class GeocodingService(ABC):
    @abstractmethod
    def geocode(self, query: str) -> Point:
        """Resolve a human-entered place to a WGS84 point."""


class FixtureGeocodingService(GeocodingService):
    LOCATIONS = {
        "provo": (-111.6585, 40.2338),
        "provo, ut": (-111.6585, 40.2338),
        "orem": (-111.6946, 40.2969),
        "orem, ut": (-111.6946, 40.2969),
        "lehi": (-111.8508, 40.3916),
        "lehi, ut": (-111.8508, 40.3916),
        "draper": (-111.8638, 40.5247),
        "draper, ut": (-111.8638, 40.5247),
        "south jordan": (-111.9297, 40.5622),
        "south jordan, ut": (-111.9297, 40.5622),
        "salt lake city": (-111.8910, 40.7608),
        "salt lake city, ut": (-111.8910, 40.7608),
    }

    def geocode(self, query: str) -> Point:
        key = " ".join(query.strip().lower().split())
        coordinates = self.LOCATIONS.get(key)
        if not coordinates:
            raise GeocodingError(
                "Location is not available in development fixtures. "
                "Try Provo, Orem, Lehi, Draper, South Jordan, or Salt Lake City, UT."
            )
        return Point(*coordinates, srid=4326)
