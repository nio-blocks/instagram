from ..instagram_search_by_user_block import InstagramSearchByUser
from ..http_blocks.rest.rest_block import RESTPolling
from unittest.mock import patch, Mock
from nio.util.support.block_test_case import NIOBlockTestCase
from requests import Response


class TestInstagramSearchByUser(NIOBlockTestCase):

    def get_test_modules(self):
        return ['logging', 'threading', 'scheduler', 'security', 'persistence']

    @patch.object(RESTPolling, "_retry")
    @patch.object(RESTPolling, "_authenticate")
    @patch.object(InstagramSearchByUser, "_extract_resource_id")
    def test_private_user(self, mock_id, mock_auth, mock_retry):
        blk = InstagramSearchByUser()
        self.configure_block(blk, {
            "queries": [
                "user1",
                "user2"
            ]
        })
        blk.queries = ['1', '2']
        blk._n_queries = len(blk.queries)
        resp = Mock()
        resp.status_code = 400
        resp.json.return_value = \
            {
                'meta': {
                    'error_type': 'APINotAllowedError',
                    'code': 400,
                    'error_message': 'you cannot view this resource'
                }
            }
        paging = False
        self.assertEqual(0, blk._idx)
        blk._retry(resp, paging)
        # skip to next idx because we are not retrying.
        self.assertEqual(1, blk._idx)

    @patch.object(RESTPolling, "_retry")
    @patch.object(RESTPolling, "_authenticate")
    @patch.object(InstagramSearchByUser, "_extract_resource_id")
    def test_retry(self, mock_id, mock_auth, mock_retry):
        blk = InstagramSearchByUser()
        self.configure_block(blk, {
            "queries": [
                "user1",
                "user2"
            ]
        })
        blk.queries = ['1', '2']
        blk._n_queries = len(blk.queries)
        resp = Mock()
        resp.status_code = 400
        paging = False
        self.assertEqual(0, blk._idx)
        blk._retry(resp, paging)
        # don't skip to next idx because we are retrying.
        self.assertEqual(0, blk._idx)
