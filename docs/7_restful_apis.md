# Restful APIs

As seen elsewhere in this guide, clearskies can automatically build a RESTful API for you with full CRUD+search functionality.  clearskies does this via the RESTful API handler, to which you pass a models class and some configuration.  the RESTful API handler will look at the schema available in your model and take care of the necessary user input checks as well as outputting the appropriate JSON.

## Configuring a RESTful API

There is a fully functional example [written with docker compose](https://github.com/cmancone/clearskies-docker-compose).  In the meantime, let's consider this example code:

```
from collections import OrderedDict
import clearskies
import clearskies_aws


class Widget(clearskies.Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            clearskies.column_types.string('name', input_requirements=[clearskies.input_requirements.required()]),
            clearskies.column_types.string('description'),
            clearskies.column_types.integer('height'),
            clearskies.column_types.integer('width'),
            clearskies.column_types.integer('length'),
        ])

class Widgets(Models):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def model_class(self):
        return Widget


api = clearskies_aws.contexts.lambda_alb(
    {
        'handler_class': clearskies.handlers.RestfulAPI,
        'handler_config': {
            'models_class': Widgets,
            'readable_columns': ['name', 'description', 'height', 'width', 'length'],
            'searchable_columns': ['name', 'description', 'height', 'width', 'length'],
            'default_sort_column': 'name',
            'authentication': clearskies.authentication.secret_bearer(secret='SECRET_API_KEY'),
        },
    },
)

def lambda_handler(event, context):
    return api(event, context)
```

We have defined the Widget model with 5 columns: name (which is required), description, height, width, and length.  We've also defined the Widgets class to go with it, which is the standard query builder/factory.  We then create a context object that represents an application running in a Lambda behind an application load balancer.  Our application is an instance of the RESTful API handler, which has some basic configuration:

1. We tell it what models class to use
2. We give it the list of readable columns - which columns from the model should be returned as part of the JSON response
3. We give it the list of writeable columns - which columns the user is allowed to set during create/update operations.
4. We provide a default sort column
5. We specify the authentication method (in this case, a hard-coded secret value that must come up via an `Authorization: Bearer [SECRET]` header.

The restful API handler has a number of additional options which we have not set here - see the docblock (TBW) on the handler class for the full details.  This includes options for making the API read only, disabling specific actions (create, update, delete), customizing the response, etc...  However, we've left the defaults in place, and so we'll end up with an API endpoint with the following routes:

## Using the API

| URL                 | HTTP Verb         | Action                                     |
|---------------------|-------------------|--------------------------------------------|
| /                   | GET               | Fetch paginated list of records            |
| /                   | POST              | Create new record                          |
| /[id]               | GET               | Fetch record by id                         |
| /[id]               | PUT               | Update record by id                        |
| /[id]               | DELETE            | Delete record by id                        |
| /search             | POST              | Search records via conditions in POST body |

In addition, all endpoints will return a JSON object with the following keys:

| name        | value                                                                                                 |
|-------------|-------------------------------------------------------------------------------------------------------|
| status      | `success` OR `clientError` OR `inputErrors` OR `failure`                                              |
| inputErrors | An dictionary with input errors.  Used only with a status of `inputErrors`, an empty string otherwise |
| error       | An error message: used only with a status of `clientError`, an empty string otherwise                 |
| data        | The actual data for the response                                                                      |
| pagination  | Information about the maximum/current size of the response                                            |

Endpoints that can return multiple records will return a JSON list for the `data` key, while the other responses will return an object.  So, for instance, a `GET` request to the `/123` endpoint might return:

```
{
  "status": "success",
  "inputErrors": [],
  "error": "",
  "pagination": {},
  "data": {
    "id": 123,
    "name": "My Example",
    "description": "Does fun things",
    "width": 100,
    "length": 100,
    "height": 100
  }
}
```

While a `GET` request to `/search` might return:

```
{
  "status": "success",
  "inputErrors": [],
  "error": "",
  "pagination": {
    "numberResults": 3,
    "start": 0,
    "limit": 100
  },
  "data": [
    {"id": 10, "name": "Some Example", "description": "", "width": 100, "length": 100, "height": 100},
    {"id": 11, "name": "Another Example", "description": "", "width": 100, "length": 100, "height": 100},
    {"id": 12, "name": "Last Example", "description": "", "width": 100, "length": 100, "height": 100}
  }
}
```

Data for the create and update request is passed in in the standard way as a JSON body:

```
curl 'https://api.example.com' -d '{"name":"My new record","width":100}' -H 'Authorization: Bearer SECRET_API_KEY'
```

The above request would be allowed since only the name field is required in the model schema.

The RESTful API will strictly check all user input, so the following request:

```
curl 'https://api.example.com' -d '{"width":"asdf"}' -H 'Authorization: Bearer SECRET_API_KEY'
```

would return a 200 status code with the following response:

```
{
  "status": "inputErrors",
  "inputErrors": {
    "name": "'name' is required.",
    "width": "width must be an integer"
  },
  "error": "",
  "data": [],
  "pagination": {}
}
```
