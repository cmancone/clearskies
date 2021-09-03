# Handlers, Applications, and Contexts, oh my!

The handler, application, and context classes work together to make sure your code can run anywhere.  Out of these, only the context is explicitly required.  Here's a quick summary of what these classes do:

### Context

A context is explicitly required to execute your code.  It's job is to normalize input and output so that your application can run the same regardless of how or where it is actually running.  It is also possible to configure details of the dependency injection container at the context level, which is often necessary to adjust behavior depending on where things are running.

### Applications

The application class has a very simple job: configure the dependency injection container.  It wraps up your handler configuration as well as the dependency injection configuration and will execute your handler when invoked by the context object.  The application class is optional: the context is capable of executing your handler without it.  However, it is often useful, as there are typically some dependency injection settings that remain the same regardless of what context your application is running in.

### Handlers

The handler class defines what to actually do.  The simplest handler is the `callable` handler and it just executes code: it accepts a function which it will call when executed.  There are also handlers for all the standard CRUD operations, a RestfulAPI handler that automatically builds a "standard" API endpoint, another to add on simple routing, one for publishing healthcheck endpoints, etc...  Handlers typically require some configuration to define the precise behavior: host a standard CRUD API endpoint for _this_ model, execute _this_ function, return a 200 status code to declare that the application is healthy as long as you can connect to _these_ backends, etc...

The handler class is a required part of clearskies execution, but it defaults to the `callable` handler if not explicitly defined (aka, it expects you to pass along a function which it will execute).

# Practical Example: Lambdas, ECS, RDS, and developer machines all working together

Let's look at a practical example.  Your company sells lightbulbs and you are responsible for the backend work to make this happen.  You've settled on the following architecture:

 1. You use an RDS to store the bulk of your product data
 2. You use ECS for your API endpoints, running your Python code via a uWSGI server (to avoid issues with cold boots for sporadic loads).  These connect to your database via credentials fetched out of SSM.
 3. A number of background processes run via Lambda.  These connect to your database via IAM Auth.
 4. Developers occassionally run processes on their local machines against the database.  These connect to the database via IAM Auth and use a bastion host to access the database.  They connect to the bastion host using SSM instead of SSH to avoid having open ports on the bastion.

### Folder Structure

Thinking about a microservice, you may have all the code for these things in one repo, so it might look like this:

```
├── app
│   ├── models
│   │   ├── __init__.py
│   │   ├── category.py
│   │   ├── categories.py
│   │   ├── product.py
│   │   └── products.py
│   │
│   ├── __init__.py
│   ├── api.py
│   ├── a_background_process.py
│   └── another_background_process.py
│
├── dev.py
├── lambda.py
├── test.py
└── wsgi.py
```

clearskies doesn't actually care how you organize your code, so you can organize it however makes sense to you.  As the name suggests though, the `models` directory contains your [model and models classes](./3_models.md).  The python files in the `app` folder contain your actual application logic - callables and API definitions.

### Application Logic

Let's look at an example of what might actually live in these files.  For instance, our `a_background_process.py` file might look like this:

```
import datetime


def a_background_process(products, now):
    # find all products that are less than a day old and do something with them
    yesterday = now - datetime.timedelta(hours=24)
    for product in products.where(f'created>{yesterday}'):
        print(f'Do something with {product.id}!')
```

`clearskies` will fill in our dependencies: the `products` variable will be an instance of `app.models.products.Products` (aka the query builder for the Product model).  `now` is a pre-defined dependency in `clearskies`, and will be a `datetime` object set to the current time.

### Context: Simple Executable

As discussed, one goal of `clearskies` is to make sure that we can run this logic from within a Lambda, in a devbox, or in a test environment, without worrying about the completely different ways that our backend connections work in those cases.  So let's see how that works for our background process!

In our root folder we have the files that are the "entry points" for execution.  Not surprisingly, the `lambda.py` file contains our lambda handlers that will be attached to a lambda, so let's see what that would look like:

```
import clearskies
import clearskies_aws
import app

background_process_in_lambda = clearskies_aws.contexts.lambda(
    app.a_background_process,
    additional_configs=clearskies_aws.di.iam_db_auth()
)

def lambda_handler(event, context):
    return background_process_in_lambda(event, context)
```

In short, we create a context for the Lambda environment.  By default, clearskies will try to connect to the database using credentials in the environment, but we want to connect via IAM Auth.  A class is available to do exactly that, so we just specify it as an additional class for dependency injection configuration.  Now though, clearskies needs to know where the RDS cluster endpoint is.  You could provide that directly to the `iam_db_auth` method, but it will also look for it in the environment as a variable named `CLUSTER_ENDPOINT`.  Therefore, this example assumes that the `CLUSTER_ENDPOINT` environment variable is being set on the Lambda and populated with the actual cluster endpoint.

Note that we define our context **outside** of the lambda handler.  If we do it like this, AWS will cache our context object for us, which means that clearskies won't have to re-initialize/re-connect to everything on each run (because the dependency injection container itself is cached by the context object).  This will improve performance overall.

Finally, we have our actual `lambda_handler` function that will be invoked by the Lambda.  This simply invokes the `background_process_in_lambda` object, passing in the event and context that AWS gave us.  In our simple example we're not using input or sending output, but of course that would not always be the case.  If our function needed to make use of input/output then we would just include `input_output` in the list of parameters, and clearskies would inject in the relevant [InputOutput](https://github.com/cmancone/clearskies/blob/master/src/clearskies/input_outputs/input_output.py) object to do exactly that.

What if we want to run this same code but from a developer machine?  Let's look at the `dev.py` file:

```
#!/usr/bin/env python3

import clearskies
import clearskies_aws
import app


background_process_in_dev_box = clearskies.contexts.cli(
    app.a_background_process,
    additional_configs=clearskies_aws.di.iam_db_auth_with_ssm_bastion(
        bastion_instance_id='i-????????',
        cluster_endpoint='mydbcluster.cluster-123456789012.us-east-1.rds.amazonaws.com:3306',
    )
)

if __name__ == '__main__':
    return background_process_in_dev_box()
```

The process looks almost identical, but with a few main differences:

1. We are now using the `clearskies.contexts.cli` context, instead of `clearskies_aws.contexts.lambda`.
2. Since we're not in a lambda, we don't have a `lambda_handler` function, and don't have `event` and `context` variables to pass in.  Fortunately, the `cli` context does not want them either.
3. We've switched out `iam_db_auth` for `iam_db_auth_with_ssm_bastion`
4. We provide the instance id of the bastion host as well as the cluster endpoint to our `iam_db_auth_with_ssm_bastion` method.  We still could have set these in the environment or in a `.env` file if we wanted to.

Otherwise though, our lambda still gets executed and it sees no differences between running locally and running in a Lambda.

### Context, Handler, and Application to build an API

Having clearskies execute a function is easy and doesn't require more than the context.  However, this changes quickly when we start looking at a more complicated application.  Let's look at how we would use clearskies to auto-generate an API endpoint for the application.  Specifically, we want to generate a RESTful API for our product.  Examining the folder structure below, we would create an application in our `app/api.py` file like so:

```
import clearskies
import clearskies_aws
from . import models


api = clearskies.Application(
    clearskies.handlers.RestfulAPI,
    {
        'models_class': models.Products,
        'readable_columns': ['name', 'description', 'price', 'created', 'updated'],
        'writeable_columns': ['name', 'description', 'price'],
        'searchable_columns': ['name', 'description', 'price'],
        'default_sort_column': 'name',
        'authentication': clearskies.authentication.public(),
    },
)
```

The RESTful API handler takes care of all the behavior we would normally have to define to create an API endpoint.  It will handle routing to decide what CRUD action is being requested, validate user input, build JSON responses, etc...  The restful API handler does all of this by building off of the schema declarations in the model.

We can also pass additional keyword arguments into the `Application` constructor (`bindings`, `binding_classes` `binding_modules`, and `additional_configs`) to declare application/dependency injection configuration just like we did in the context before. This allows us to provide defaults for our applications, but these settings can still be overriden at the context layer.  We haven't bothered specifying any such configuration settings here, because by default clearskies expects to use simple credentials to connect to the database, which is what we want our API endpoints to do.  We just need to provide these credentials in environment variables (see the documentation on the [cursor backend](./6_cursor_backend.md) for more details on that).

To create the API endpoint we just need to attach the application to a WSGI context and execute it from a WSGI handler. This happens in the `wsgi.py` file and looks like this:

```
import clearskies
import app


api = clearskies.contexts.wsgi(app.api)

def wsgi_handler(env, start_response):
    return api(env, start_response)
```

And that's it!  Previously we attached our function directly to the context, but the context will also except [clearskies.Application](https://github.com/cmancone/clearskies/blob/master/src/clearskies/application.py) objects.  Once again, we create the context outside of our handler function so that the WSGI server can cache it.  Inside the WSGI function we simply execute our context and pass in the `env` and `start_response` variables that came from the WSGI server: the wsgi context requires these and will take care of normalizing input and output for our application.

A few months later though, you decide that you're tired of running a WSGI server in ECS and want to switch to a Lambda.  To keep things simple you will launch it behind an application load balancer and also want to use IAM Auth like everywhere else.  That's not a problem at all, and changes like this are why the context is separate from the application.  You would just drop this into a file:

```
import clearskies_aws
import app


api = clearskies_aws.contexts.lambda_alb(
    app.api,
    additional_configs=clearskies_aws.di.iam_db_auth(),
)

def lambda_handler(event, context):
    return api(event, context)
```

If you then decide that you also want your devs to run the API endpoint on their local machine via WSGI while connected to the production backend using IAM Auth through a bastion (because, why not???) then you just need to follow the same basic steps as our previous dev box setup:

```
import clearskies
import clearskies_aws
import app


background_process_context = clearskies.contexts.wsgi(
    app.api,
    additional_configs=clearskies_aws.di.iam_db_auth_with_ssm_bastion(
        bastion_instance_id='i-????????',
        cluster_endpoint='mydbcluster.cluster-123456789012.us-east-1.rds.amazonaws.com:3306',
    )
)

def wsgi_handler(env, start_response):
    return api(env, start_response)
```

Just point the local WSGI server to the `wsgi_handler` in this file, and you'll be running a test endpoint locally that operates against the production database.  Of course you may not want to run against the production database, so let's run the production application against an in-memory data store when it runs locally:

```
import clearskies
import app


background_process_context = clearskies.contexts.wsgi(app.api)
background_process_context.bind('cursor_backend', clearskies.backends.MemoryBackend)

def wsgi_handler(env, start_response):
    return api(env, start_response)
```

Now we don't have to worry about accidentally breaking production!

### A Note About Dependency Injection

The above examples work assuming that clearskies can automatically discover your classes for dependency injection.  This will often be the case.  In general though, it works as long as you have your `__init__.py` files import everything.  In other words, your `app/models/__init__.py` file would look like this:

```
from .category import Category
from .categories import Categories
from .product import Product
from .products import Products
```

and your `app/__init__.py` file would look like this:

```
from . import models
from .api import API
from .lambda import lambda
from .a_background_process import a_background_process
from .another_background_process import another_background_process
```

If you do this and do a simple `import app` at the top of the actual files you run, then clearskies will automatically find all your classes for dependency injection.  You can also manually specify classes and modules for DI as well as turn off the automatic import using simple flags when you build the context:

```
background_process_context = clearskies.contexts.cli(
    your_executable,
    binding_classes = [SomeClass, AnotherClass],
    binding_modules = [some_module, another_module],
    auto_inject_loaded_modules = False,
)
```

More details are available in the section about [dependency injection](./10_dependency_injection.md).

Next: [Backends](./6_backends.md)
