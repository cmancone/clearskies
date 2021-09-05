# Simple Routing

The RESTful API handler comes with some basic routing built in, and if that was all you ever needed then you would be good to go!  Except, that's never how things work.  Routing in clearskies is taken care of by handlers.  There are a couple varities for different use cases, but the most common one is the [simple_routing](../src/clearskies/handlers/simple_routing.py) handler.  This allows you to build your application by attaching other handlers to endpoints.

Specifically, you configure the simple routing handler by providing a list of routes.  Each route contains the handler class and handler configuration to execute, and then (optionally) the path parameter and/or request method to match.  When a request comes in, the simple routing handler starts at the "top" of the routes list and works down, executing the given handler if the requested URL matches the route.  If no matches are found then a standard 404 respose is returned.

## Example

Consider a case where you have two RESTful API endpoints: the end-user has full CRUD control for users, and can also read the list of user statuses.  Configuring such an application with the simple routing handler would look like this:

```
import clearskies
from . import models


users_statuses_api = clearskies.Application(
    clearskies.handlers.SimpleRouting,
    {
        'authentication': clearskies.authentication.public(),
        'schema_route': 'schema',
        'routes': [
            {
                'path': 'users',
                'handler_class': clearskies.handlers.RestfulAPI,
                'handler_config': {
                    'models_class': models.Users,
                    'readable_columns': ['status_id', 'name', 'email', 'created', 'updated'],
                    'writeable_columns': ['status_id', 'name', 'email'],
                    'searchable_columns': ['status_id', 'name', 'email'],
                    'default_sort_column': 'name',
                },
            },
            {
                'path': 'statuses',
                'handler_class': clearskies.handlers.RestfulAPI,
                'handler_config': {
                    'read_only': True,
                    'models_class': models.Statuses,
                    'readable_columns': ['name', 'users'],
                    'searchable_columns': ['name', 'users'],
                    'default_sort_column': 'name',
                },
            },
            {
                'path': 'healthcheck',
                'handler_class': clearskies.handlers.HealthCheck,
                'handler_config': {
                    'verify': ['cursor_backend']
                }
            }
        ],
    },
)
```

We've specified public authentication in the root of the simple routing configuration, which means that this will be the default for the application: you can override this in the handler configuration of individual routes.

This gives us four primary "sections" to our application (3 declared routes plus a `/schema` endpoint that is automatically created when we specify the `schema_route` configuration option):

| URL base path | Behavior                                                  |
|---------------|-----------------------------------------------------------|
| /schema       | Automatically generated OAI3.0 document for all endpoints |
| /users        | RESTful API endpoints for users model                     |
| /statuses     | read-only API endpoint for status model                   |
| /healthcheck  | A healthcheck endpoint                                    |

It's also important to know that handlers called by the simple routing handler can also do their own routing, so this would give you the endpoints you expect: `GET /users`, `POST /users`, `GET /users/[id]`, `GET /statuses`, etc...

This also means that simple routing handlers can be nested, which is made easier because they can also accept an application object.  Therefore, we could build off of this first set of routes like so:

```
versioned_api = clearskies.Application(
    clearskies.handlers.SimpleRouting,
    {
        'authentication': clearskies.authentication.public(),
        'schema_route': 'schema',
        'routes': [
            {
                'path': 'v0',
                'application': users_statuses_api # the application we declared above
            },
            {
                'path': 'v1',
                'application: some_other_application,
            }
        ]
    }
)
```

This will move all of our previous routes like so:

| URL base path    | Behavior                                                  |
|------------------|-----------------------------------------------------------|
| /v0/schema       | Automatically generated OAI3.0 document for all endpoints |
| /v0/users        | RESTful API endpoints for users model                     |
| /v0/statuses     | read-only API endpoint for status model                   |
| /v0/healthcheck  | A healthcheck endpoint                                    |

The `/v0/shcema` route will only return the Open API3.0 schema for things under the `/v0/` route, but we will have a new `/schema` endpoint which includes the schema for _all_ the routes in the application.  In addition, we'll have a new `/v1` route that includes whatever is declared inside `some_other_application`.  You could then attach these applications to any context you needed:

```
versioned_api_in_lambda = clearskies_aws.contexts.lambda_alb(versioned_api)

def lambda_handler(event, context):
    return versioned_api_in_lambda(event, context)
```

or

```
old_api_in_wsgi = clearskies.contexts.wsgi(users_statuses_api)
def wsgi_handler(env, start_response):
    return old_api_in_wsgi(env, start_response)
```
