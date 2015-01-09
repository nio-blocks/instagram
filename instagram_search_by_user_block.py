from .instagram_search_by import InstagramSearchByBase
from nio.common.discovery import Discoverable, DiscoverableType


@Discoverable(DiscoverableType.block)
class InstagramSearchByUser(InstagramSearchByBase):

    """ This block polls the Instagram API, searching for all posts
    by the specified users.

    Params:
        client_id (string): api credentials.
        lookback (timedelta): amount of time to lookback for posts on start.

    """

    # Count max is currently 33 on Instagram
    # Try to grab 50 in case they up the limit
    URL_FORMAT = ("https://api.instagram.com/v1/users"
                  "/{0}/media/recent?count=50&client_id={1}&min_timestamp={2}")

    RESOURCE_URL_FORMAT = ("https://api.instagram.com/v1/"
                           "users/search?q={0}&client_id={1}")

    def _extract_resource_id(self, users, query):
        print(users)
        for user in users:
            if user.get('username').lower() == query.lower():
                _id = user.get('id', None)
                self._logger.debug("Got id {0} for user {1}"
                                   .format(_id, query))
                self.persistence.store(query.lower(), _id)
                return _id
