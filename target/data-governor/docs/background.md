# Background

`data-governor` is an application written in Python using the [Flask](http://flask.pocoo.com) microframework. It is responsible 
for mananging *state* information of data pipeline jobs. It consists of a series of *HTTP endpoints*, each of 
which are used to either:

1. Inform the system of a state change
1. Request information about the current state of the pipeline

## Proposed Implementation

`data-governor` is meant to be one-half of a two-system replacement for DMF.
`data-governor`'s sister system is `data-executor`, responsible for scheduling
and dispatching jobs. Until the latter system is written, however,
`data-governor` will assume part of the role of job executor. In the future,
though, `data-governor` will only be responsible for maintaing and reporting 
state; job execution will be handled by `data-executor`.

## System Architecture

`data-governor` consists of a series of HTTP endpoints, all of which are
extensively covered in this document. Each endpoint inherits
from a single `Endpoint` base class. The `Endpoint` class contains mechanisms
to list *required* and *optional* endpoint parameters, 
the URL and human-readable name of the endpoint, and various utility methods for ensuring
that `data-governor` always responds with proper HTTP status codes and messages.

Each endpoint class defines all HTTP methods that are valid for the particular
endpoint. Requests are routed to methods based on request method name, so HTTP
GET requests are handled by a `def get()` method, while HTTP POST requests would
be handled by a `def post()` method. All other HTTP methods are considered
invalid for the endpoint.

At the time of this writing, endpoints are synchronous. 
An HTTP POST request to the `/log` endpoint, for example, will query and update 
the DMF database in a blocking manner. While `data-executor` will eventually be 
responsible for all "execution" of this type, `celery` will be used to
facilitate asynchronous requests.

Though generally orthogonal, all endpoints share a connection to a *memcached*
cache containing request statistics. These statistics are available at the
`/view_status` endpoint. `/view_status` contains a number of useful metrics
about the process, as well as process configuration settings and currently
active endpoints.

### HTTP Return Codes

One major area in which `data-governor` functionality diverges from the DMF 
application is in the use HTTP status codes. In DMF, all service requests
respond with HTTP 200 (OK), regardless of whether the request was successfully
handled. 

`data-governor` responds with the proper HTTP codes in all scenarios. Note that
this means, for example, one can not rely on HTTP 200 being the only status code
indicating success. `HTTP 200`, `HTTP 201`, `HTTP 202`, and `HTTP 204` are all
valid success return codes within `data-governor`. Similarly `data-governor`
replies with the proper error codes when an error condition is encountered. For
a full list of possible error codes and their meaning, see the documentation for
the `exception` module.

Lastly, `data-governor` performs content-negotiation, honors `Accepts`
headers, and return the proper `Content-Type` header value. Not that this is
different from DMF, which returns `Content-Type: text/html` even when returning
JSON.
