# clearskies

clearskies is a Python framework intended for developing microservices in the cloud via declarative programming principles.  It is mainly intended for backend services and havs built-in support for RESTful API endpoints, queue listeners, scheduled tasks, and the like.

# Installation and Usage

```
pip3 install clear-skies
```

For usage examples see:

[https://github.com/cmancone/clearskies-docker-compose](https://github.com/cmancone/clearskies-docker-compose)

# Overview

clearskies is really just a set of loosely coupled classes that play nicely with eachother and coordinate via dependency injection.  The primary goals of this framework include:

 - [Context neutral: your applications run them same whether they are in a lambda, queue listener, behind a WSGI server, or run locally via the CLI](context-neutral)
 - [Extreme flexibility: all apsects of the framework can be easily replaced via sideloading](sideloading)
 - [Creating backend APIs via declarative principles, rather than "direct" programming](declarative-apis)
 - [Secrets Management/Dynamic credentials as a first-class citizen](secrets-management)
 - [Ease of testing](testing)

But what does that actually mean?

### Context Neutral

Executing code in clearskies starts with an "application": a combination of code and configuration that can be run anywhere.  In order to run an application, you attach it to the appropriate "context": WSGI server, Lambda, CLI, test environment, etc...  The context abstracts away the details of input output as well as execution, so the application runs the same regardless.  This means, for instance, that what runs as an API endpoint behind a WSGI server can be moved to a Lambda by changing a single line of code, or even be turned into a self-documenting CLI tool just as easily.  A "cron" task that runs in a lambda triggered via CloudWatch can also be executed locally via the CLI, and can also be easily executed as part of your integration tests.

### Sideloading

Modifying "standard" clearksies behavior via sideloading opens up a world of options.  For instance, like most frameworks, clearskies assumes that your database credentials are hard-coded in environment variables or a `.env` file.  However, what if you have an application that wants to connect to an AWS RDS via IAM auth?  No problem!  There is a class for that.  It takes just one line of code to drop it into your application configuration, and then clearskies adjusts its behavior in a transparent fasion that is completely invisible to the rest of your application.  Do you want to run tasks locally while connected to your database via IAM Auth while tunneling the connection through a bastion host via SSM?  Do you want some of your models to not even connect to a database at all, but instead use an external API as if it was a database?  Easy.  Sideloading makes this simple to manage, because you can define common "modes" of working that suit your needs in a shared library, and therefore adjust the behavior of clearskies without actually having to make any changes to the framework code itself.

### Declarative APIs

Creating APIs via [declarative programming principles](https://en.wikipedia.org/wiki/Declarative_programming) means that you tell clearskies what you want done instead of how to do it.  In short, you just create your model class which declares the properties of your data structure, and then declare an API endpoint and describe a few details about it.  clearskies will then generate a fully functional API endpoint!  Of course, this is an optional feature, and you can always manage your own API endpoints in more standard ways.

clearskies can also automatically generate the swagger docs for your APIs, simplifying integration.

### Secrets Management

Secret management is often neglected in the early days of application development, and many startups ignore it until poor secret hygiene causes a public breach.  The reality though is that proper secret management actually _simplifies_ application development and should be encouraged from the start.  As a result, clearskies integrates with modern secret managment platforms to simplify application management.  For instance, take [AKeyless](https://akeyless.io), which has a number of options to solve the secret-zero problem.  Your cloud infrastructure can use [IAM Auth](to create a streamlined) to login to AKeyless, your Gitlab pipelines can use their `CI_JOB_JWT` to [login via OAuth2](https://docs.akeyless.io/docs/openid), your developers can [use SAML](https://docs.akeyless.io/docs/saml), and on-prem infrastructure can use [universal identity](https://docs.akeyless.io/docs/universal-identity).  clearskies supports this by allowing you to easily adjust the process used to login to the secret manager at runtime, which means that your workloads are able to access the necessary secrets regardless of where they run, and do so by logging in exclusively with short-lived, dynamic credentials.

Finally, clearskies also supports the use of [dynamic secrets](https://docs.akeyless.io/docs/how-to-create-dynamic-secret) where appropriate, meaning that you can create application deployments that don't rely on any static secrets at all, with minimal fuss.

### Testing

clearskies aims to simplify testing with two key methods: dependency injection and configurable backends.  The first is hardly a new concept, but the second item is worth expanding on.  As part of the sideloading capabilities, clearskies does not make any assumptions about how your models store and retrieve data.  In many frameworks, integration tests work by spinning up an actual database for the application to connect to, with tables cleared/reset between tests.  In clearskies, the models make no assumptions at all about what kind of system data is stored in.  As a result, during testing, the "typical" SQL database backend is automatically swapped out for an in-memory backend.  This change is transparent to your models and requires absolutely no infrastructure, dramatically simplifying testing.

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

You would also create a query builder/model factory:

```
from clearskies import Models
from . import product


class Products(Models):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def model_class(self):
        return product.Product
```

You then need to create your application.  This includes a handler+configuration (which tells clearskies what *kind* of behavior to execute) and, optionally, some basic configuration for the dependency injection container:

```
import clearskies
import models


products_api = clearskies.Application(
    clearskies.handlers.RestfulAPI,
    {
        'authentication': clearskies.authentication.public(),
        'models_class': models.Products,
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
