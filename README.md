# clearskies
clearskies is a microframework intended especially for developing applications in the cloud.  However, even calling it a microframework is a bit of a stretch.  It's really just a set of classes that work well together and which are tied together on an as-needed basis via dependency injection.  It's definitely **not** your typical framework, as it tries to automate a completely different list of things.  If you are used to "standard" frameworks then you'll find that this is missing a lot of the tools you take for granted, while helping with other things you never asked a framework to do for you.  Therefore, this probably isn't the tool for you.

# Inside the Box

 - Fairly standard models and query builder
 - Support for MySQL-like backends
 - Ability to use external APIs as a backend
 - Automatic generation of API endpoints via declarative coding conventions
 - Built-in conventions for proper secret storage in environment + secret manager
 - Bare-minimum routing capabilities
 - Absolutely everything is configurable and replaceable

# Not Included

 - Built in webserver (That's what lambdas, queue managers, and simple WSGI servers are for)
 - More advanced routing options (microservices probably don't need much routing, and load balancers can handle the rest)
 - Views, templates, content management
 - Anything that even remotely resembles a front end
 - Log handling
 - Basically anything not listed in the "Inside the Box" section above

# Upcoming

 - Rules engine for user-configurable notifications/actions
 - Integration with [mygrations](https://github.com/cmancone/mygrations) - stateless database migration system
 - Automatic API documentation generator
