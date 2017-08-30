Instagram
=========
Polls Instagram for public posts, given a hashtag. The hashtag can be in either the caption or comments. Official documentation of [Instagram API hashtags](http://instagram.com/developer/endpoints/tags/).

Properties
----------
- **creds**: API credentials.
- **include_query**: Whether to include queries in request to Instagram.
- **polling_interval**: How often Instagram is polled. When using more than one query. Each query will be polled at a period equal to the *polling interval* times the number of queries.
- **queries**: List of hashtags to search public posts for.
- **retry_interval**: When a url request fails, how long to wait before attempting to try again.
- **retry_limit**: Number of times to retry on a poll.
- **safe_mode**: If true, queries will not return content marked as sensative

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: Creates a new signal for each Instagram Post. Every field on the Post will become a signal attribute. Official documentation on the repsonse fields from Instagram [here](http://instagram.com/developer/endpoints/tags/).

Commands
--------
None

Dependencies
------------
-   [requests](https://pypi.python.org/pypi/requests/)
-   [RESTPolling Block](https://github.com/nio-blocks/http_blocks/blob/master/rest/rest_block.py)

InstagramSearchByLocation
=========================
Polls Instagram for public posts at a specified location. Official documentation of [User Instagram API](http://instagram.com/developer/endpoints/users/).

Properties
----------
- **client_id**: Client ID from Instagram API account
- **include_query**: Whether to include queries in request to Instagram.
- **lookback**: On block start, look back this amount of time to grab old posts.
- **polling_interval**: How often Instagram is polled. When using more than one query. Each query will be polled at a period equal to the *polling interval* times the number of queries.
- **queries**: List of locations to search public posts for.
- **retry_interval**: When a url request fails, how long to wait before attempting to try again.
- **retry_limit**: Number of times to retry on a poll.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: Creates a new signal for each Instagram Post. Every field on the Post will become a signal attribute. Official documentation on the repsonse fields from Instagram [here](http://instagram.com/developer/endpoints/tags/).

Commands
--------
None

Dependencies
------------
-   [requests](https://pypi.python.org/pypi/requests/)
-   [RESTPolling Block](https://github.com/nio-blocks/http_blocks/blob/master/rest/rest_block.py)

InstagramSearchByRadius
=======================
Polls Instagram for public posts in a specified radius around latitudes/longitudes. Official documentation of [User Instagram API](http://instagram.com/developer/endpoints/users/).

Properties
----------
- **client_id**: Client ID from Instagram API account
- **include_query**: Whether to include queries in request to Instagram.
- **lookback**: On block start, look back this amount of time to grab old posts.
- **polling_interval**: How often Instagram is polled. When using more than one query. Each query will be polled at a period equal to the *polling interval* times the number of queries.
- **queries**: List of latitudes, longitudes, and radii to search public posts for.
- **retry_interval**: When a url request fails, how long to wait before attempting to try again.
- **retry_limit**: Number of times to retry on a poll.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: Creates a new signal for each Instagram Post. Every field on the Post will become a signal attribute. Official documentation on the repsonse fields from Instagram [here](http://instagram.com/developer/endpoints/tags/).

Commands
--------
None

Dependencies
------------
-   [requests](https://pypi.python.org/pypi/requests/)
-   [RESTPolling Block](https://github.com/nio-blocks/http_blocks/blob/master/rest/rest_block.py)

InstagramSearchByUser
=====================
Polls Instagram for public posts by a specified user. Official documentation of [User Instagram API](http://instagram.com/developer/endpoints/users/).

Properties
----------
- **client_id**: Client ID from Instagram API account
- **include_query**: Whether to include queries in request to Instagram.
- **lookback**: On block start, look back this amount of time to grab old posts.
- **polling_interval**: How often Instagram is polled. When using more than one query. Each query will be polled at a period equal to the *polling interval* times the number of queries.
- **queries**: List of latitudes, longitudes, and radii to search public posts for.
- **retry_interval**: When a url request fails, how long to wait before attempting to try again.
- **retry_limit**: Number of times to retry on a poll.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: Creates a new signal for each Instagram Post. Every field on the Post will become a signal attribute. Official documentation on the repsonse fields from Instagram [here](http://instagram.com/developer/endpoints/tags/).

Commands
--------
None

Dependencies
------------
-   [requests](https://pypi.python.org/pypi/requests/)
-   [RESTPolling Block](https://github.com/nio-blocks/http_blocks/blob/master/rest/rest_block.py)

Output
------
Creates a new signal for each Instagram Post. Every field on the Post will become a signal attribute. Official documentation on the repsonse fields from Instagram [here](http://instagram.com/developer/endpoints/tags/). The following is a list of commonly include attributes, but note that not all will be included on every signal:

Output Example
--------------
```
{
  id: string,
  user: {
    username: string
  },
  caption: {
    text: string
  },
  link: string,
  images: {
    standard_resolution: {
      url: string,
      width: int,
      height: int
    }
  },
  user: {
    profile_picture: string,
    id: string
  },
  type: string,
  created_time: string
}
```

