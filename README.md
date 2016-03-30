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


## Contents

- [Features](#features)
- [Overview](#overview)
- [API Endpoints](#api-endpoints)
- [Deployment](#deployment)
- [Development](#development)


## Features

- Fully compatible with GitHub OAuth2 (no need to maintain users and
  passwords!)

- Based on AWS API Gateway, Lambda, and DynamoDB (no servers to manage!)

- Specially designed for client-side single page javascript apps (Ember, React,
  etc)


## Overview

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


## API Endpoints

- `/auth/token`: Responsible for doing to the token validation and exchange.

- `/auth/refresh`: Responsible for exchanging an almost-expired JSON Web Token
for a new one.

- `/auth/ping`: Return the currently running version of the Lambda function.


## Deployment


#### Create the DynamoDB table:

- Table Name: `<DYNAMODB TABLE NAME>`
- Primary Key: `user_id` (type: `Number`)

(you may leave the other options as default if you wish)


#### Create an IAM role with a policy that looks something like:

``` json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "sns:Publish",
                "sns:Subscribe"
            ],
            "Resource": [
                "arn:aws:logs:*:*:*",
                "arn:aws:sns:*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "dynamodb:*",
            "Resource": "arn:aws:dynamodb:<AWS REGION>:<AWS ACCOUNT ID>:table/<DYNAMODB TABLE NAME>"
        }
    ]
}
```

#### Create the Lambda function:

- Name: `tidycat-auth-backend`
- Runtime: `Python 2.7`
- Upload zip file: [lambda.zip](https://github.com/tidycat/auth-backend/releases/latest)
- Handler: `auth_backend/entrypoint.handler`
- Role: _IAM role you created earlier_
- Memory: 128 MB
- Timeout: 30 seconds


#### Setup API Gateway:

Create the following API Gateway resources and methods:

``` text
/
  /auth
    /token
      POST
    /refresh
      POST
    /ping
      GET
```

You will need to run through the following numbered items for _EACH_ of the
methods above:

1. Choose an **Integration type** of _Lambda Function_ and point it at the
   `tidycat-auth-backend` Lambda function.

1. Create the following **Body Mapping Templates** for the method's
   **Integration Request**:

    Content-Type: `application/json`

    ``` json
    {
      "resource-path": "$context.resourcePath",
      "payload": $input.json('$'),
      "jwt_signing_secret": "${stageVariables.jwt_signing_secret}",
      "oauth_client_id": "${stageVariables.oauth_client_id}",
      "oauth_client_secret": "${stageVariables.oauth_client_secret}",
      "auth_dynamodb_endpoint_url": "${stageVariables.auth_dynamodb_endpoint_url}",
      "auth_dynamodb_table_name": "${stageVariables.auth_dynamodb_table_name}",
      "auth_desired_oauth_scopes": "${stageVariables.auth_desired_oauth_scopes}"
    }
    ```

1. Add the following **Method Response** entries, with corresponding **Response
   Models** of `application/json: Empty`.

    - 200
    - 400
    - 401
    - 500

1. Create the following **Integration Response** entries:

    | Lambda Error Regex       | Method response status | Default mapping | BMT Content-Type   | BMT Template                    |
    | ------------------       | ---------------------- | --------------- | ----------------   | ------------                    |
    | _blank_                  | 200                    | Yes             | `application/json` | `$input.json('$.data')`         |
    | `.*"http_status":.400.*` | 400                    | No              | `application/json` | `$input.path('$.errorMessage')` |
    | `.*"http_status":.401.*` | 401                    | No              | `application/json` | `$input.path('$.errorMessage')` |
    | `.*"http_status":.500.*` | 400                    | No              | `application/json` | `$input.path('$.errorMessage')` |

    _Note: BMT = Body Mapping Templates_

After all that is done for each of the methods, we can finally move on to the
stage variables portion. Ensure that the following **Stage Variables** are set
appropriately:

- `jwt_signing_secret`
- `oauth_client_id`
- `oauth_client_secret`
- `auth_dynamodb_endpoint_url` (e.g. `https://dynamodb.us-east-1.amazonaws.com`)
- `auth_dynamodb_table_name`
- `auth_desired_oauth_scopes` (e.g. `user:email,notifications`)

This will seem cumbersome and thankfully doesn't need to be revisited very
often. If there is a reasonable way to automate this setup, I'm game!


## Development

#### Tools

- Python 2.7.11 (AWS Lambda needs 2.7.x)
- Java runtime 6.x or newer (for the local DynamoDB instance)

#### Environment Variables

- `OAUTH_CLIENT_ID` (GitHub [application][4] ID)
- `OAUTH_CLIENT_SECRET` (GitHub [application][4] secret)
- `DYNAMODB_ENDPOINT_URL` (e.g. `https://dynamodb.us-east-1.amazonaws.com`)
- `DYNAMODB_TABLE_NAME` (e.g. `tidycat-auth-backend`)
- `DESIRED_OAUTH_SCOPES` (e.g. `"user:email,notifications"`)

#### Workflow

First and foremost, have a read through all the targets in the Makefile. I've
opted for the [self-documentation][5] approach so issue a `make` and have a
look at all your options.

You can run the local test server while developing instead of deploying to AWS
and testing there (`make server`). If you need to re-initialize the local
DynamoDB instance, first run `make local-dynamodb` and after that is up and
running, `make init-local-dynamodb` (in another terminal window).

That should give you a pretty decent local environment to develop in!

[Bug reports][6] or [contributions][7] are always welcome.


[1]: https://developer.github.com/v3/oauth/#web-application-flow
[2]: https://jwt.io
[3]: https://github.com/jpadilla/ember-simple-auth-token
[4]: https://github.com/settings/applications/new
[5]: http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
[6]: https://github.com/tidycat/auth-backend/issues
[7]: https://github.com/tidycat/auth-backend/pulls
