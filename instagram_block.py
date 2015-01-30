from .http_blocks.rest.rest_block import RESTPolling
from nio.common.discovery import Discoverable, DiscoverableType
from nio.metadata.properties import PropertyHolder, StringProperty, \
    ObjectProperty, BoolProperty
from nio.common.signal.base import Signal
import requests


class APICredentials(PropertyHolder):
    client_id = StringProperty(title="Client ID",
                               default="[[INSTAGRAM_CLIENT_ID]]")


class InstagramSignal(Signal):

    def __init__(self, data):
        super().__init__()
        for k in data:
            setattr(self, k, data[k])


@Discoverable(DiscoverableType.block)
class Instagram(RESTPolling):

    """ This block polls the Instagram API, searching for posts
    matching a configurable hashtag.

    Params:
        creds (APICredentials): API credentials

    """

    # Count max is currently 33 on Instagram
    # Try to grab 50 in case they up the limit
    URL_FORMAT = ("https://api.instagram.com/v1/tags"
                  "/{0}/media/recent?count=50&client_id={1}&min_tag_id={2}")

    creds = ObjectProperty(APICredentials, title='Credentials')
    safe_mode = BoolProperty(title='Safe Mode', default=True)

    def __init__(self):
        super().__init__()
        self._min_tag_id = [None]
        self._prev_min_tag_id = [None]

    def configure(self, context):
        super().configure(context)
        self._min_tag_id *= self._n_queries
        self._prev_min_tag_id *= self._n_queries

    def start(self):
        self._initialize_all_min_tag_ids()
        super().start()

    def _prepare_url(self, paging=False):
        """ Overridden from RESTPolling block.

        Appends the Cliend ID to the format string. Adds the min_tag_id to
        only get results since last poll. When paging, url is already
        provided so just add the min_tag_id.

        Args:
            paging (bool): Are we paging?

        Returns:
            None

        """
        # If there is no min_tag_id, then this is likely the first poll and
        # we need to initialize the min_tag_id.
        if self.min_tag_id is None:
            self._initialize_min_tag_id()
        if not paging:
            # New query so save off the new min_tag_id.
            self.prev_min_tag_id = self.min_tag_id
            self.url = self.URL_FORMAT.format(self.current_query,
                                              self.creds.client_id,
                                              self.prev_min_tag_id)
        else:
            self.url = "%s&min_tag_id=%s" % (self.url, self.prev_min_tag_id)
        self._logger.info("GETing url: {0}".format(self.url))

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
        posts = resp['data']
        pagination = resp['pagination']

        self._update_min_tag_id(pagination)
        paging = self._check_paging(pagination)

        for post in posts:
            signals.append(InstagramSignal(post))
        self._logger.info("Created {0} new Instagram signals.".format(
            len(signals)))

        return signals, paging

    def _get_post_id(self, post):
        return getattr(post, 'id', None)

    def _initialize_all_min_tag_ids(self):
        with self._poll_lock:
            for id in range(0, self._n_queries):
                self._initialize_min_tag_id()
                self._idx = (self._idx + 1) % self._n_queries

    def _initialize_min_tag_id(self):
        try:
            self.min_tag_id = 0
            url = self.URL_FORMAT.format(self.current_query,
                                         self.creds.client_id,
                                         self.min_tag_id)
            resp = requests.get(url)
            resp = resp.json()
            self.min_tag_id = resp['pagination']['min_tag_id']
            self._logger.debug("Initialized min_tag_id to {0} for query: {1}"
                               .format(self.min_tag_id, self.current_query))
            # And make a second request since the initial min_tag_id is
            # not always accurate the first time. Try it and see for yourself!
            url = self.URL_FORMAT.format(self.current_query,
                                         self.creds.client_id,
                                         self.min_tag_id)
            resp = requests.get(url)
            resp = resp.json()
            pagination = resp['pagination']
            self._update_min_tag_id(pagination)
        except Exception:
            self._logger.warning(
                "Failed to initialize min_tag_id for query: {0}. url: {1}"
                .format(self.current_query, url))
            self.min_tag_id = None

    def _update_min_tag_id(self, pagination):
        if 'min_tag_id' in pagination and pagination['min_tag_id'] > \
                self.min_tag_id:
            self.min_tag_id = pagination['min_tag_id']
            self._logger.debug("Updating min_tag_id to {0} for query: {1}"
                               .format(self.min_tag_id, self.current_query))

    def _check_paging(self, pagination):
        if self.safe_mode and \
                self.page_num >= self.polling_interval.total_seconds():
            # Don't let a single query page too many times if in safe mode.
            self._logger.warning("Safe Mode: #{} is paging too many times:"
                                 " {}".format(self.current_query,
                                              self.page_num)
                                 )
            return False
        if 'next_url' in pagination:
            self.url = pagination['next_url']
            return True
        else:
            return False

    @property
    def min_tag_id(self):
        return self._min_tag_id[self._idx]

    @min_tag_id.setter
    def min_tag_id(self, val):
        self._min_tag_id[self._idx] = val

    @property
    def prev_min_tag_id(self):
        return self._prev_min_tag_id[self._idx]

    @prev_min_tag_id.setter
    def prev_min_tag_id(self, val):
        self._prev_min_tag_id[self._idx] = val
