from .instagram_search_by import InstagramSearchByBase
from nio.util.discovery import discoverable


@discoverable
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
        for user in users:
            if user.get('username').lower() == query.lower():
                _id = user.get('id', None)
                self.logger.debug("Got id {0} for user {1}"
                                   .format(_id, query))
                return _id

    def _on_failure(self, resp, paging, url):
        execute_retry = True
        try:
            status_code = resp.status_code
            resp = resp.json()
            err_type = resp.get('meta', {}).get('error_type')
            if status_code == 400 and \
               err_type in ['APINotAllowedError', 'APINotFoundError']:
                self.logger.debug(
                    "Skipping private user: {}".format(self.current_query))
                execute_retry = False
                self._increment_idx()
        finally:
            self.logger.error(
                "Polling request of {} returned status {}: {}".format(
                    url, status_code, resp)
            )
            if execute_retry:
                self._retry(paging)
