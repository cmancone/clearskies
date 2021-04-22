# clearskies

clearskies is a Python-based micro-framework intended for developing microservices in the cloud via declarative programming principles.  It is mainly intended for RESTful API endpoints, queue listeners, runners, and the like.

# Overview

clearskies is really just a set of loosely coupled classes that play nicely with eachother and coordinate via dependency injection.  It's definitely **not** your typical framework, as it tries to automate a completely different list of things.  If you are used to "standard" frameworks then you'll find that this is missing a lot of the tools you take for granted, while helping with other things you never asked a framework to do for you.

It's built on [declarative programming principles](https://en.wikipedia.org/wiki/Declarative_programming), which means that you tell clearskies what you want done instead of how to do it.  In short, you just create your model class which declares the properties of your data structure, and then declare an API endpoint and describe a few details about it.  clearskies will then generate a fully functional API endpoint!  Of course, there are also easy ways to inject in your own behavior with standard OOP principles when the declarative options provided by clearskies don't work for you.

# Installation and Usage

```
pip3 install clear-skies
```

For usage examples see:

[https://github.com/cmancone/clearskies-docker-compose](https://github.com/cmancone/clearskies-docker-compose)

# Simple Example

For a simple example of using clearskies, imagine you need an API endpoint to allow clients to manage a list of users.  You want to keep track of the name, email, age, and created/updated timestamps for each user in an SQL database, and have some input requirements for the API.  You would declare a model like this:

```
from collections import OrderedDict
from clearskies import Model
from clearskies.column_types import string, email, integer, created, updated
from clearskies.input_requirements import Required, MaximumLength


class User(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            string('name', input_requirements=[Required, (MaximumLength, 255)]),
            email('email', input_requirements=[Required, (MaximumLength, 255)]),
            integer('age'),
            created('created'),
            updated('updated'),
        ])
```

And would also create a query builder/model factory:

```
from clearskies import Models
from user import User


class Users(Models):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def model_class(self):
        return User
```

Assuming you were hooking this up with a WSGI server, you would then create and publish a WSGI-compatible application like this:

```
import clearskies
from users import Users
from user import User


def application(env, start_response):
    api = clearskies.binding_specs.WSGI.init_application(
        clearskies.handlers.RestfulAPI,
        {
            'models_class': Users,
            'readable_columns': ['name', 'email', 'age', 'created', 'updated'],
            'writeable_columns': ['name', 'email', 'age'],
            'searchable_columns': ['name', 'email', 'age'],
            'default_sort_column': 'name',
            'authentication': clearskies.authentication.public(),
        },
        env,
        start_response,
    )
    return api()
```

You now have a standard RESTful API with CRUD operations!  This includes detailed input errors for end users, strict input checking, and a search options.

For more details and a working example that you can spin up via docker-compose, just see the documentation:

[https://github.com/cmancone/clearskies-docker-compose/tree/master/example_1_restful_users](https://github.com/cmancone/clearskies-docker-compose/tree/master/example_1_restful_users)

# Inside the Box

 - Fairly standard models and query builder
 - Support for MySQL-like backends
 - Ability to use external APIs as a backend
 - Automatic generation of API endpoints via declarative coding conventions
 - Built-in conventions for proper secret storage in environment and/or secret manager
 - Simple routing
 - Extensive validation of configuration provided by developer and easy-to-understand error messages
 - Extensive user input validation and easy-to-understand error messages
 - Explicit Authentication for API Endpoints
 - Easy lifecycle hooks for full customization
 - Absolutely everything can be customized and modified - no part of clearskies is required

# Upcoming features

 - Stateless database migrations via [mygrations](https://github.com/cmancone/mygrations)
 - User-configurable rules engine
 - Auto generated swagger documentation
 - Easy Authorization

# Not Included

 - Built in webserver (That's what lambdas, and simple WSGI servers are for)
 - More advanced routing options (microservices don't need much routing, and load balancers/API gateways can handle the rest)
 - Log handling - that's what cloudwatch and log aggregators are for
 - Views, templates, content management
 - Anything that even remotely resembles a front end
 - Basically anything not listed in the "Inside the Box" section above
