# Handlers, Applications, and Contexts, oh my!

The handler, application, and context classes work together to make sure your code can run anywhere.  Out of these, only the context is explicitly required.  Here's a quick summary of what these classes do:

### Handlers

The handler class defines the general behavior to execute.  The simplest handler just executes code: it accepts a function which it will call when executed.  There are also handlers for all the standard CRUD operations, a RestfulAPI handler that automatically builds a "standard" API endpoint, another to add on simple routing, one for publishing healthcheck endpoints, etc...  Handlers typically require some configuration to define the precise behavior: host a standard CRUD API endpoint for _this_ model, execute _this_ function, you're healthy as long as you can connect to _these_ backends, etc...

While the handler is optional, it can also be defined implicitly.  Specifically, if you attach a function to an application, clearskies will default to the standard "callable" handler which executes your function when the application is invoked.

### Applications

The application class has a very simple job: configure the dependency injection container.  It wraps up your handler configuration as well as the dependency injection confiugration and will execute your handler when invoked by the context object.  The application class is optional: the context is capable of executing your handler without it.  However, it is often useful, as there is typically some dependency injection configuration that remains the same regardless of what context your application is running in.  This will become clearer after discussing the context:

### Context

A context is explicitly required to execute your code.  It's job is to normalize input and output so that your application can run the same regardless of how or where it is actually running.  It is also possible to configure details of the dependency injection container at the context level, which is often necessary to adjust behavior depending on where things are running.

# Practical Example: Lambdas, ECS, RDS, and developer machines all working together

Let's look at a practical example.  Your company sells lightbulbs and you are responsible for the backend work to make this happen.  You've settled on the following architecture:

 1. You use an RDS to store the bulk of your product data
 2. You use ECS for your API endpoints, running your Python code via a uWSGI server (to avoid issues with cold boots for sporadic loads)
 3.
