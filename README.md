# Authentication Backend

[![Travis CI](https://img.shields.io/travis/tidycat/auth-backend/master.svg?style=flat-square)](https://travis-ci.org/tidycat/auth-backend)
[![Code Coverage](https://img.shields.io/coveralls/tidycat/auth-backend/master.svg?style=flat-square)](https://coveralls.io/github/tidycat/auth-backend?branch=master)
[![MIT License](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat-square)](LICENSE.txt)

This AWS Lambda authentication backend is intended to be a [JSON Web
Token][2]-based authentication and authorization backend. It uses GitHub as the
primary authentication mechanism (via OAuth2) and validates and refreshes JSON
Web Tokens as needed.

It has been designed to be fully compatible with the [Ember Simple Auth
Token][3] addon.


### Features

- Fully compatible with GitHub OAuth2 (no need to maintain users and
  passwords!)

- Based on AWS API Gateway, Lambda, and DynamoDB (no servers to manage!)

- Specially designed for client-side single page javascript apps (Ember, React,
  etc)


### Architecture

- Documentation WIP


### Development

- Documentation WIP


### Overview

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

- `/auth/ping`: Return the currently running version of the Lambda function.


[1]: https://developer.github.com/v3/oauth/#web-application-flow
[2]: https://jwt.io
[3]: https://github.com/jpadilla/ember-simple-auth-token
