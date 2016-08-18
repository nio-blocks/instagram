from .instagram_search_by import InstagramSearchByBase
from nio.util.discovery import discoverable
from nio.properties.list import ListProperty
from nio.properties.int import IntProperty
from nio.properties.float import FloatProperty
from nio.properties.holder import PropertyHolder


class LocationRadius(PropertyHolder):
    radius = IntProperty(title='Radius (m)', default=1000)
    latitude = FloatProperty(title='Latitude', default=0.0)
    longitude = FloatProperty(title='Longitude', default=0.0)


@discoverable
class InstagramSearchByRadius(InstagramSearchByBase):

    """ This block polls the Instagram API, searching for all posts
    by the specified users.

    Params:
        client_id (string): api credentials.
        lookback (timedelta): amount of time to lookback for posts on start.

    """

    # Count max is currently 33 on Instagram
    # Try to grab 50 in case they up the limit
    URL_FORMAT = ("https://api.instagram.com/v1/media"
                  "/search?{0}&count=50&client_id={1}&min_timestamp={2}")

    queries = ListProperty(LocationRadius, title='Locations')

    def __init__(self):
        super().__init__()
        self._created_field = 'created_time'

    def _process_query(self, query):
        """ Convert LocationRadius objects into lat/lng api parameters.

        """
        params = "lat={0}&lng={1}&distance={2}"
        return params.format(query.latitude(), query.longitude(), query.radius())

    @property
    def current_query(self):
        return self.queries[self._idx]
