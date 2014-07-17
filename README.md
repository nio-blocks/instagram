Instagram
=======

Get public posts from Instgram. These blocks will poll the instgram api at the configured interval. Search by hashtag or username.

-   [Instagram](https://github.com/nio-blocks/instagram#instagram)
-   [InstagramSearchByUser](https://github.com/nio-blocks/instagram#instagramsearchbyuser)

***

Instagram
=========

Polls Instagram for public posts, given a hashtag. The hashtag can be in either the caption or comments. Official documentation of Instagram API [here](http://instagram.com/developer/endpoints/tags/).

Properties
--------------

-   **queries**: List of hashtags to search public posts for.
-   **creds**: API credentials.
-   **polling_interval**: How often API is polled. When using more than one query. Each query will be polled at a period equal to the *polling\_interval* times the number of queries.
-   **retry_interval**: When a url request fails, how long to wait before attempting to try again.
-   **retry_limit**: When a url request fails, number of times to attempt a retry before giving up.

Dependencies
----------------

-   [requests](https://pypi.python.org/pypi/requests/)
-   [RESTPolling Block](https://github.com/nio-blocks/http_blocks/blob/master/rest/rest_block.py)

Commands
----------------
None

Input
-------
None

Output
---------
Creates a new signal for each Instagram Post. Every field on the Post will become a signal attribute. Official documentation on the repsonse fields from Instagram [here](http://instagram.com/developer/endpoints/tags/). The following is a list of commonly include attributes, but note that not all will be included on every signal:

-   id
-   user['username']
-   caption['text']
-   link
-   images['standard_resolution']['url']
-   user['profile_picture']
-   type
-   created_time

***

InstagramSearchByUser
=========

Polls Instagram for public posts by a specified user. Official documentation of Instagram API [here](http://instagram.com/developer/endpoints/users/).

Properties
--------------

-   **queries**: List of users to search public posts for.
-   **cliend_id**: API credentials.
-   **polling_interval**: How often API is polled. When using more than one query. Each query will be polled at a period equal to the *polling\_interval* times the number of queries.
-   **retry_interval**: When a url request fails, how long to wait before attempting to try again.
-   **retry_limit**: When a url request fails, number of times to attempt a retry before giving up.
-   **lookback**: On start, lookback this amount of time and grab old posts.

Dependencies
----------------

-   [requests](https://pypi.python.org/pypi/requests/)
-   [RESTPolling Block](https://github.com/nio-blocks/http_blocks/blob/master/rest/rest_block.py)

Commands
----------------
None

Input
-------
None

Output
---------
Creates a new signal for each Instagram Post. Every field on the Post will become a signal attribute. Official documentation on the repsonse fields from Instagram [here](http://instagram.com/developer/endpoints/tags/). The following is a list of commonly include attributes, but note that not all will be included on every signal:

-   id
-   user['username']
-   caption['text']
-   link
-   images['standard_resolution']['url']
-   user['profile_picture']
-   type
-   created_time
