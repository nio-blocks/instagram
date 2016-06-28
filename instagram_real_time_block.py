from nio.block.mixins.web_server.web_server_block import WebServer
from nio.block.base import Block
from nio.util.discovery import discoverable
from nio.common.versioning.dependency import DependsOn
from nio.properties.holder import PropertyHolder
from nio.properties.string import StringProperty
from nio.properties.object import ObjectProperty
from nio.properties.timedelta import TimeDeltaProperty
from nio.properties.list import ListProperty
from nio.properties.int import IntProperty
from nio.signal.base import Signal
from nio.modules.web import RESTHandler
from nio.modules.scheduler import Job
from threading import Lock, spawn
import requests
from urllib.request import quote
from time import time
import uuid


class APICredentials(PropertyHolder):
    client_id = StringProperty(title="Client ID",
                               default="[[INSTAGRAM_CLIENT_ID]]")
    client_secret = StringProperty(title="Client Secret",
                                   default="[[INSTAGRAM_CLIENT_SECRET]]")


class ServerInfo(PropertyHolder):
    host = StringProperty(title='Host', default='[[NIOHOST]]')
    port = IntProperty(title='Port', default=8182)
    endpoint = StringProperty(title='Endpoint', default='')


class InstagramSignal(Signal):

    def __init__(self, data):
        for k in data:
            setattr(self, k, data[k])


class SubscriptionHandler(RESTHandler):

    def __init__(self, endpoint, poll, logger):
        super().__init__('/' + endpoint)
        self._schedule_poll = poll
        self.logger = logger
        self.counter = 0

    def on_post(self, req, rsp):
        t = time()
        self.logger.debug("Subscription handling POST: {} {}".format(req, t))
        body = req.get_body()
        for subscription in body:
            self.counter += 1
            subscription_id = subscription.get('subscription_id')
            if subscription_id:
                spawn(self._schedule_poll, int(subscription_id))

    def on_get(self, req, rsp):
        self.logger.debug(
            "Subscription handling GET: {}"
            .format(req.get_params().get('hub.challenge'))
        )
        rsp.set_body(req.get_params().get('hub.challenge'))


@DependsOn("nio.modules.web", "1.0.0")
@discoverable
class InstagramRealTime(Block, WebServer):

    """ This block polls the Instagram real-time API, searching
    for posts matching a configurable hashtag.

    Params:
        creds (APICredentials): API credentials

    """

    # Count max is currently 33 on Instagram
    # Try to grab 50 in case they up the limit
    URL_FORMAT = ("https://api.instagram.com/v1/tags"
                  "/{0}/media/recent?count=50&client_id={1}&min_tag_id={2}")

    creds = ObjectProperty(APICredentials, title='Credentials')
    queries = ListProperty(str, title='Query Strings')
    server_info = ObjectProperty(ServerInfo, title='Server Callback')
    external_url = StringProperty(title='External URL', default='')
    polling_interval = TimeDeltaProperty(title='Polling Interval')

    def __init__(self):
        super().__init__()
        self._n_queries = 1
        self._url = None
        self._idx = 0
        self._poll_lock = Lock()
        self._schedule_poll_lock = Lock()
        self._poll_job = [None]
        self._recent_posts = {}
        self._subscription_id = {}
        self._min_tag_id = [None]
        self._prev_min_tag_id = [None]

    def configure(self, context):
        super().configure(context)
        self._n_queries = len(self.queries) or 1
        self._poll_job *= self._n_queries
        self._min_tag_id *= self._n_queries
        self._prev_min_tag_id *= self._n_queries
        # configure web server
        conf = {
            'host': self.server_info.host,
            'port': self.server_info.port
        }
        self.configure_server(conf,
                              SubscriptionHandler(self.server_info.endpoint,
                                                  self._schedule_poll,
                                                  self.logger),
                              )

    def start(self):
        super().start()
        # Start Web Server
        self.start_server()
        # don't let polling start until all subscriptions are ready.
        with self._poll_lock:
            self._initialize_all_min_tag_ids()
            self._create_subscriptions()

    def stop(self):
        super().stop()
        self._delete_subscriptions()
        for job in self._poll_job:
            if job is not None:
                job.cancel()
        # Stop Web Server
        self.stop_server()

    def _schedule_poll(self, subscription_id):
        # If a poll is not already scheduled, run poll and schedule one.
        self.logger.debug('SCHED {}'.format(subscription_id))
        id = uuid.uuid1()
        self.logger.debug('{}'.format(id))
        with self._schedule_poll_lock:
            self.logger.debug('{}'.format(id))
            idx = self._subscription_id.get(subscription_id)
            if not self._poll_job[idx]:
                self.logger.debug(
                    "Scheduling poll job for {}"
                    .format(subscription_id)
                )
                spawn(self.poll(subscription_id))
                self._poll_job[idx] = Job(
                    self._scheduled_poll,
                    self.polling_interval,
                    False,
                    subscription_id=subscription_id
                )
            else:
                self.logger.debug(
                    "Discarding poll job for {}"
                    .format(subscription_id)
                )

    def _scheduled_poll(self, subscription_id):
        # When a scheduled poll runs, first release the job.
        with self._schedule_poll_lock:
            idx = self._subscription_id.get(subscription_id)
            self._poll_job[idx] = None
            self.logger.debug(
                "Running scheduled poll job for {}"
                .format(subscription_id)
            )
        self.poll(subscription_id)

    def poll(self, subscription_id):
        self.logger.debug(
            "Polling for {}"
            .format(subscription_id)
        )
        with self._poll_lock:
            # set idx for this poll so we use the right query, url, etc.
            self._idx = self._subscription_id.get(subscription_id)
            # if the subscription is not found, then delete it.
            if self._idx is None:
                self._delete_subscription(subscription_id)
                return
            # paging is False when starting a new poll
            paging = False
            polling = True
            while polling:
                # assume we are not polling again unless explicitly set.
                polling = False
                headers = self._prepare_url(paging)
                url = self.url
                first_page = not paging

                self.logger.debug("%s: %s" %
                                   ("Paging" if paging else "Polling", url))

                try:
                    resp = requests.get(url, headers=headers)
                except Exception as e:
                    self.logger.error("GET request failed, details: %s" % e)
                    return

                status = resp.status_code
                self.etag = self.etag if paging \
                    else resp.headers.get('ETag')
                self.modified = self.modified if paging \
                    else resp.headers.get('Last-Modified')

                if status != 200 and status != 304:
                    self.logger.error(
                        "Polling request returned status %d" % status
                    )
                else:
                    # process the Response object and initiate paging if
                    # necessary
                    try:
                        signals, paging = self._process_response(resp)
                        signals = self._discard_duplicate_posts(
                            signals, first_page
                        )
                        if signals:
                            self.notify_signals(signals)
                        polling = paging
                    except Exception as e:
                        self.logger.error(
                            "Error while processing polling response: %s" % e
                        )

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
        self.logger.info("GETing url: {0}".format(self.url))

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
        self.logger.info("Created {0} new Instagram signals.".format(
            len(signals)))

        return signals, paging

    def _get_post_id(self, post):
        return getattr(post, 'id', None)

    def _create_subscriptions(self):
        for id in range(0, self._n_queries):
            self._idx = id
            self._create_subscription()

    def _create_subscription(self):
        url = "https://api.instagram.com/v1/subscriptions/"
        client_id = self.creds.client_id
        client_secret = self.creds.client_secret
        object = 'tag'
        aspect = 'media'
        object_id = self.current_query
        callback_url = "http://{0}:{1}/{2}".format(
            self.server_info.host,
            self.server_info.port,
            self.server_info.endpoint
        )
        # use the external url if one has been set
        callback_url = self.external_url or callback_url
        payload = {'client_id': client_id,
                   'client_secret': client_secret,
                   'object': object,
                   'aspect': aspect,
                   'object_id': object_id,
                   'callback_url': callback_url}
        try:
            self.logger.debug(
                "Creating subscription for {}".format(object_id)
            )
            resp = requests.post(url, data=payload)
            resp = resp.json()
            subscription_id = resp.get('data', {}).get('id')
            if subscription_id:
                self._subscription_id[int(subscription_id)] = self._idx
                self.logger.debug(
                    "Subscription created for {}: {}".format(
                        self.current_query,
                        subscription_id
                    )
                )
            else:
                self.logger.debug(
                    "Bad subscription response: {}".format(resp)
                )
        except Exception as e:
            self.logger.error(
                "Error creating subscription: {}".format(e)
            )

    def _delete_subscriptions(self):
        for subscription_id in self._subscription_id:
            self._delete_subscription(subscription_id)

    def _delete_subscription(self, subscription_id):
        self.logger.debug(
            "Deleting subscription: {}".format(subscription_id)
        )
        url = "https://api.instagram.com/v1/subscriptions?"
        url += "client_secret={}&client_id={}&id={}".format(
            self.creds.client_secret,
            self.creds.client_id,
            subscription_id
        )
        requests.delete(url)
        # self._subscription_id.pop(subscription_id, None)

    def _initialize_all_min_tag_ids(self):
        for id in range(0, self._n_queries):
            self._idx = id
            self._initialize_min_tag_id()

    def _initialize_min_tag_id(self):
        try:
            self.min_tag_id = 0
            url = self.URL_FORMAT.format(self.current_query,
                                         self.creds.client_id,
                                         self.min_tag_id)
            resp = requests.get(url)
            resp = resp.json()
            self.min_tag_id = resp['pagination']['min_tag_id']
            self.logger.debug("Initialized min_tag_id to {0} for query: {1}"
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
            self.logger.warning(
                "Failed to initialize min_tag_id for query: {0}. url: {1}"
                .format(self.current_query, url))
            self.min_tag_id = None

    def _update_min_tag_id(self, pagination):
        if ('min_tag_id' in pagination and
                pagination['min_tag_id'] > self.min_tag_id):
            self.min_tag_id = pagination['min_tag_id']
            self.logger.debug("Updating min_tag_id to {0} for query: {1}"
                               .format(self.min_tag_id, self.current_query))

    def _check_paging(self, pagination):
        if 'next_url' in pagination:
            self.url = pagination['next_url']
            return True
        else:
            return False

    def _discard_duplicate_posts(self, posts, first_page):
        """ Removes sigs that were already found by another query.

        Each query acts independently so if a post matches multiple
        queries, then it will be notified for each one. This method
        keeps track of the all the most recent posts for each query
        and discards posts if they are already here.

        Args:
            posts (list(dict)): A list of posts.
            first_page (bool): True if this is the first page of query.

        Returns:
            posts (list(dict)): The amended list of posts.

        """
        # No need ot try to discards posts if there is only one query.
        if self._n_queries <= 1:
            return posts

        # If first page of query, clear recent_posts for this query.
        if first_page:
            self._recent_posts[self._idx] = set()
        # Return only posts that are not in self._recent_posts.
        return_posts = []
        for post in posts:
            post_id = self._get_post_id(post)
            if post_id:
                # Only keep post if id has not been seen recently.
                unique_post = True
                for recent_posts in self._recent_posts:
                    if post_id in self._recent_posts[recent_posts]:
                        unique_post = False
                        break
                if unique_post:
                    return_posts.append(post)
                self._recent_posts[self._idx].add(post_id)
            else:
                # No unique id so keep the post.
                return_posts.append(post)

        return return_posts

    @property
    def current_query(self):
        return quote(self.queries[self._idx])

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url):
        self._url = url

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
