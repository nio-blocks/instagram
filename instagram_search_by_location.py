import re

from nio.properties import VersionProperty

from .instagram_search_by import InstagramSearchByBase


class InstagramSearchByLocation(InstagramSearchByBase):

    """ This block polls the Instagram API, searching for all posts
    by the specified users.

    Params:
        client_id (string): api credentials.
        lookback (timedelta): amount of time to lookback for posts on start.

    """

    # Count max is currently 33 on Instagram
    # Try to grab 50 in case they up the limit
    URL_FORMAT = ("https://api.instagram.com/v1/locations"
                  "/{0}/media/recent?count=50&client_id={1}&min_timestamp={2}")

    version = VersionProperty("0.0.1")
    RESOURCE_URL_FORMAT = ("https://api.instagram.com/v1"
                           "/locations/search?{0}&client_id={1}")

    def __init__(self):
        super().__init__()
        self._created_field = 'created_time'
        self._latlong = re.compile('-?[0-9\.]*,\s?-?[0-9\.]*$')

    def _construct_resource_url(self, query):
        resource_url = self.RESOURCE_URL_FORMAT
        if self._latlong.match(query) is not None:
            lat, lng = re.sub('\s', '', query).split(',')
            resource_url = resource_url.format(
                'lat={0}&lng={1}'.format(lat, lng),
                self.client_id())

        else:
            resource_url = resource_url.format(
                'facebook_places_id={}'.format(query),
                self.client_id())

        return resource_url

    def _extract_resource_id(self, locations, query):
        if locations:
            _id = locations[0].get('id', None)
            self.logger.debug("Got id {0} for resource {1}".format(_id, query))
            return _id
