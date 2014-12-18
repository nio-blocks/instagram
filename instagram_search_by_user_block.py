from .http_blocks.rest.rest_block import RESTPolling
from nio.common.discovery import Discoverable, DiscoverableType
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.timedelta import TimeDeltaProperty
from nio.common.signal.base import Signal
from datetime import datetime
import requests


class InstagramSignal(Signal):

    def __init__(self, data):
        for k in data:
            setattr(self, k, data[k])


@Discoverable(DiscoverableType.block)
class InstagramSearchByUser(RESTPolling):

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

    USER_URL_FORMAT = ("https://api.instagram.com/v1/"
                       "users/search?q={0}&client_id={1}")

    client_id = StringProperty(name="Client ID",
                               default="[[INSTAGRAM_CLIENT_ID]]")
    lookback = TimeDeltaProperty()

    def __init__(self):
        super().__init__()
        self._created_field = 'created_time'

    def configure(self, context):
        super().configure(context)
        lb = self._unix_time(datetime.utcnow() - self.lookback)
        self._freshest = [lb] * self._n_queries
        # Convert queries from usernames to ids.
        self.queries = [i for i in [self._convert_query_to_id(q)
                        for q in self.queries] if i]
        # reset n in case some usernames did not convert to ids.
        self._n_queries = len(self.queries) or 1

    def _prepare_url(self, paging=False):
        # if paging then url is already set in _check_paging()
        if not paging:
            self.url = self.URL_FORMAT.format(
                self.current_query,
                self.client_id,
                self.freshest
            )

    def _process_response(self, resp):
        """ Extract fresh posts from the Instagram api response object.

        Args:
            resp (Response)

        Returns:
            signals (list(Signal)): The list of signals to notify, each of
                which corresponds to a fresh Instagram post.
            paging (bool): Denotes whether or not paging requests are
                necessary.

        """
        signals = []
        resp = resp.json()

        pagination = resp['pagination']
        paging = self._check_paging(pagination)

        fresh_posts = posts = resp.get('data', [])
        if len(posts) > 0:
            self.update_freshness(posts)
            fresh_posts = self.find_fresh_posts(posts)

        signals = [InstagramSignal(p) for p in fresh_posts]
        self._logger.info("Created {0} new Instagram signals.".format(
            len(signals)))

        return signals, paging

    def _get_post_id(self, post):
        return getattr(post, 'id', None)

    def _retry(self, resp, paging):
        resp_error_type = resp.json().get('meta', {}).get('error_type')
        if resp.status_code == 400 and resp_error_type == 'APINotAllowedError':
            # this is a private user, skip to next query.
            self._logger.debug("Skipping private user: {}".format(
                self.current_query))
            self._increment_idx()
        else:
            super()._retry(resp, paging)

    def _check_paging(self, pagination):
        if 'next_url' in pagination:
            self.url = pagination['next_url']
            return True
        else:
            return False

    def _convert_query_to_id(self, query):
        """ Queries need to be converted from username to id.

        Instagram api queries by user need a user id as a parameter.
        This block asks has a parameter for usernames so on start,
        requests to the instagram api need to be made to convert
        username to id.
        """
        user_url = self.USER_URL_FORMAT.format(
            query,
            self.client_id)
        resp = self._make_request(user_url)
        if resp is None:
            # try again if the response was bad.
            self._logger.debug("Attempting immediate retry to get id"
                               " for: {0}".format(query))
            resp = self._make_request(user_url)
            if resp is None:
                # if the response is still bad, give up.
                return

        users = resp.json().get('data', [])
        for user in users:
            if user.get('username').lower() == query.lower():
                id = user.get('id', None)
                self._logger.debug("Got id {0} for user {1}"
                                   .format(id, query))
                return id

    def _make_request(self, url):
        try:
            resp = requests.get(url)
        except Exception as e:
            self._logger.error("GET request failed: {0}".format(e))
            return
        status = resp.status_code
        if status != 200 and status != 304:
            self._logger.error(
                "Instagram request returned status %d" % status
            )
            return
        return resp

    def _parse_date(self, date):
        """ Overriden from base block."""
        return datetime.utcfromtimestamp(int(date))
