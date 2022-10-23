# clearskies

clearskies is a very opinionated Python framework intended for developing microservices in the cloud via declarative programming principles.  It is mainly intended for backend services and so is designed for RESTful API endpoints, queue listeners, scheduled tasks, and the like.

# Installation, Documentation, and Usage

To install:

```
pip3 install clear-skies
```

Documentation lives here:

[https://github.com/cmancone/clearskies/tree/master/docs](./docs)

For usage examples see:

[https://github.com/cmancone/clearskies-docker-compose](https://github.com/cmancone/clearskies-docker-compose)

# Overview

clearskies is really just a set of loosely coupled classes that play nicely with eachother and coordinate via dependency injection.  The primary goals of this framework include:

 - [Truly Reusable business logic](#reusable-business-logic)
 - [Context neutral: your applications run them same whether they are in a lambda, queue listener, behind a WSGI server, or run locally via the CLI](#context-neutral)
 - [Extreme flexibility: all apsects of the framework can be easily replaced via sideloading](#sideloading)
 - [Creating backend APIs via declarative principles, rather than "direct" programming](#declarative-apis)
 - [Secrets Management/Dynamic credentials as a first-class citizen](#secrets-management)
 - [Ease of testing](#testing)

But what does that actually mean?

### Reusable Business Logic

A key goal of clearskies is to make business logic as easy to reuse as possible.  Since it's a primary goal, [there is an entire page devoted to it in the documentation](./docs/2_but_why.md).

### Context Neutral

Executing code in clearskies starts with an "application": a combination of code and configuration that can be run anywhere.  In order to run an application, you attach it to the appropriate "context": WSGI server, Lambda, Queue listener, CLI, test environment, etc...  The same code can run in your production environment, on a dev machine, or in your test suite without making any changes.

### Sideloading

Every aspect of clearskies is meant to be modified and this is controlled by replacing classes via configuration.  Do you want to connect to an RDS via IAM auth instead of static credentials?  Do you want some of your models to store data in memory, some to fetch/save data to an external API, and some to connect via IAM auth to an RDS in a private subnet by using an SSM tunnel through a bastion?  No problem.  Define your behavior once and re-use it everywhere without issue.

### Declarative APIs

Creating APIs via [declarative programming principles](https://en.wikipedia.org/wiki/Declarative_programming) means that you tell clearskies what you want done instead of how to do it.  Create your models and tell clearskies which columns to expose.  From there, clearskies will generate a fully functional API endpoint!  It will even automatically generate your [OAI3.0/Swagger](https://swagger.io/specification/) docs.  It can even host them from your application so that your docs automatically update themselves as you push out changes.

### Secrets Management

clearskies integrates tightly with your secret management system to bring secrets back _into_ the application.  By fetching secrets at run time, clearskies works smoothly with dynamic credentials and can also re-fetch static secrets automatically as needed.  This means that you can safely modify secrets in your secret manager as needed without having to worry about coordinating with the re-deployment of your application.

### Testing

In addition to the use of dependency injection to simplify testing, clearskies also uses its sideloading capabilities to switch out your SQL backend during tests. By switching your typical SQL backend for an in-memory backend, your models and requires absolutely no infrastructure, dramatically simplifying testing.

# Simple Example

For a simple example of using clearskies, imagine you need an API endpoint to allow clients to manage a list of products.  You want to keep track of the name, description, cost, and created/updated timestamps for each product in an SQL database.  You also have some input requirements for the API.  You would declare a model like this:

```
from collections import OrderedDict
from clearskies import Model
from clearskies.column_types import string, email, float, created, updated
from clearskies.input_requirements import required, maximum_length


class Product(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            string('name', input_requirements=[required(), maximum_length(255)]),
            string('description', input_requirements=[required(), maximum_length(1024)]),
            float('price'),
            created('created'),
            updated('updated'),
        ])
```

You then need to create your application.  This includes a handler+configuration (which tells clearskies what *kind* of behavior to execute) and, optionally, some basic configuration for the dependency injection container:

```
import clearskies
import models


products_api = clearskies.Application(
    clearskies.handlers.RestfulAPI,
    {
        'authentication': clearskies.authentication.public(),
        'model_class': models.Product,
        'readable_columns': ['name', 'description', 'price', 'created', 'updated'],
        'writeable_columns': ['name', 'description', 'price'],
        'searchable_columns': ['name', 'description', 'price'],
        'default_sort_column': 'name',
    },
    binding_modules=[models]
)
```

This application defines a "standard" RESTful API with CRUD endpoints (including search+pagination), detailed input errors for end users, and strict configuration checking for developers.  It informs the dependency injection container about the `models` module, so that our model classes can all be injected automatically.

To run this, we just need to attach the application to a context.  If running in a WSGI server you would just:

```
import clearskies
from applications import products_api


api = clearskies.contexts.wsgi(products_api)
def application(env, start_response):
    return api(env, start_response)
```

If you wanted to run it in a Lambda behind an load balancer, you would just do this:

```
import clearskies
from applications import products_api


api = clearskies.contexts.aws_lambda_elb(products_api)
def application(event, context):
    return api(event, context)
```

and you can even turn it into a command line executable:

```
#!/usr/bin/env python3
import clearskies
from applications import products_api


cli = clearskies.contexts.cli(products_api)
cli()
```

For more details and a working example that you can spin up via docker-compose, just see the usage documentation:

[https://github.com/cmancone/clearskies-docker-compose/tree/master/example_1_restful_users](https://github.com/cmancone/clearskies-docker-compose/tree/master/example_1_restful_users)

# Inside the Box

 - Fairly standard models and query builder
 - Support for MySQL-like backends
 - Ability to use external APIs as a backend
 - In-memory backend
 - Automatic generation of API endpoints via declarative coding conventions
 - Built-in conventions for proper secret storage in environment and/or secret manager
 - Simple routing
 - Extensive validation of configuration provided by developer and easy-to-understand error messages
 - Extensive user input validation and easy-to-understand error messages
 - Explicit Authentication
 - Easy lifecycle hooks for full customization
 - Absolutely everything can be customized and modified - no part of clearskies is required
 - Stateless database migrations via [mygrations](https://github.com/cmancone/mygrations)
 - Auto generated swagger documentation
 - Easy Authorization

# Upcoming features

 - User-configurable rules engine

# Not Included

 - Built in webserver (That's what lambdas, and simple WSGI servers are for)
 - More advanced routing options (microservices don't need much routing, and load balancers/API gateways can handle the rest)
 - Views, templates, content management
 - Anything that even remotely resembles a front end
 - Basically anything not listed in the "Inside the Box" section above
