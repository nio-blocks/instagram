from .http_blocks.rest.rest_block import RESTPolling
from nio.properties.string import StringProperty
from nio.properties.timedelta import TimeDeltaProperty
from nio.signal.base import Signal
from datetime import datetime
import requests


class InstagramSearchByBase(RESTPolling):

    """ This block polls the Instagram API, searching for all posts
    by the specified users.

    Params:
        client_id (string): api credentials.
        lookback (timedelta): amount of time to lookback for posts on start.

    """

    client_id = StringProperty(name="Client ID",
                               default="[[INSTAGRAM_CLIENT_ID]]")
    lookback = TimeDeltaProperty()

    RESOURCE_URL_FORMAT = None

    def __init__(self):
        super().__init__()
        self._created_field = 'created_time'

    def configure(self, context):
        super().configure(context)
        lb = self._unix_time(datetime.utcnow() - self.lookback)
        self._freshest = [lb] * self._n_queries
        # Convert queries from usernames to ids.
        self.queries = [i for i in [self._process_query(q)
                        for q in self.queries] if i]
        # reset n in case some usernames did not convert to ids.
        self._n_queries = len(self.queries)

    def stop(self):
        self.persistence.save()
        super().stop()

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

        pagination = resp.get('pagination', [])
        paging = self._check_paging(pagination)

        fresh_posts = posts = resp.get('data', [])
        if len(posts) > 0:
            self.update_freshness(posts)
            fresh_posts = self.find_fresh_posts(posts)

        signals = [Signal(p) for p in fresh_posts]
        self.logger.info("Created {0} new Instagram signals.".format(
            len(signals)))

        return signals, paging

    def _get_post_id(self, post):
        return getattr(post, 'id', None)

    def _check_paging(self, pagination):
        if 'next_url' in pagination:
            self.url = pagination['next_url']
            return True
        else:
            return False

    def _process_query(self, query):
        """ Queries need to be converted from username to id.

        Instagram api queries by user need a user id as a parameter.
        This block asks has a parameter for usernames so on start,
        requests to the instagram api need to be made to convert
        username to id.

        """
        # If there is a cached id for this user, return it
        # and skip the request
        _id = self.persistence.load(query.lower())
        if _id is not None:
            return _id
        
        resource_url = self._construct_resource_url(query)
        
        resp = self._make_request(resource_url)
        if resp is None:
            # try again if the response was bad.
            self.logger.debug("Attempting immediate retry to get id"
                               " for: {0}".format(query))
            resp = self._make_request(resource_url)
            if resp is None:
                # if the response is still bad, give up.
                return

        resources = resp.json().get('data', [])
        return self._extract_resource_id(resources, query)

    def _extract_resource_id(self, resources, query):
        """ This should be overridden in child blocks.

        Defines the mechanism for extracting resource ids from
        a (list of) resources.

        """
        return 

    def _construct_resource_url(self, query):
        if self.RESOURCE_URL_FORMAT is not None:
            return self.RESOURCE_URL_FORMAT.format(
                query,
                self.client_id)

    def _make_request(self, url):
        try:
            resp = requests.get(url)
        except Exception as e:
            self.logger.error("GET request failed: {0}".format(e))
            return
        status = resp.status_code
        if status != 200 and status != 304:
            self.logger.error(
                "Instagram request returned status %d" % status
            )
            return
        return resp

    def _parse_date(self, date):
        """ Overriden from base block."""
        return datetime.utcfromtimestamp(int(date))
