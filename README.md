# Authentication Backend

[![Travis CI](https://img.shields.io/travis/tidycat/auth-backend/master.svg?style=flat-square)](https://travis-ci.org/tidycat/auth-backend)
[![Code Coverage](https://img.shields.io/coveralls/tidycat/auth-backend/master.svg?style=flat-square)](https://coveralls.io/github/tidycat/auth-backend?branch=master)
[![MIT License](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat-square)](LICENSE.txt)

The role of this backend will be to exchange [temporary GitHub access
tokens][1] for [JSON Web Tokens][2]. The idea here is that a client-side
javascript app will handle the initial GitHub authorization portion, after
which it communicates with this backend to exchange that temporary access code
for a JWT.

A high level overview of how this works:

1. A human authorizes the Tidy Cat GitHub application access to some of their
   personal information (using a `Login with GitHub` action).

1. Upon authorization, GitHub redirects the client back with an `access token`.

1. The client then passes this `access token` along to this authorization
   backend.

1. The authorization backend exchanges this `access token` (with GitHub) for a
   bearer token, stores that bearer token on behalf of the client, and then
   returns a signed JWT back to the client.


### API Endpoints

- `/auth/token`: Responsible for doing to the token validation and exchange.

- `/auth/refresh`: Responsible for exchanging an almost-expired JSON Web Token
for a new one.


### Scheduled Tasks

This backend will also be responsible for periodically ensuring that the stored
bearer token is still valid.


[1]: https://developer.github.com/v3/oauth/#web-application-flow
[2]: https://jwt.io
