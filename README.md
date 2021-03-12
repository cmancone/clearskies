# clearskies

clearskies is a Python-basd nano-framework intended for developing microservices in the cloud.  It is mainly intended for RESTful API endpoints, queue listeners, runners, and the like.

## Seriously, a nano framework?

Why do I call this a nano-framework?  Because it would be a stretch to call this a micro framework - it's really just a set of loosely coupled classes that play nicely with eachother, and which coordinate via dependency injection.  It's definitely **not** your typical framework, as it tries to automate a completely different list of things.  If you are used to "standard" frameworks then you'll find that this is missing a lot of the tools you take for granted, while helping with other things you never asked a framework to do for you.  Therefore, this probably isn't the tool for you.

# Installation and Usage

```
pip3 install clear-skies
```

# Inside the Box

 - Fairly standard models and query builder
 - Support for MySQL-like backends
 - Ability to use external APIs as a backend
 - Automatic generation of API endpoints via declarative coding conventions
 - Built-in conventions for proper secret storage in environment + secret manager
 - Method-based routing capabilities
 - Extensive user input validation and easy-to-understand error messages
 - Explicit Authentication for API Endpoints
 - Easy Authorization
 - Easy lifecycle hooks for plug-and-play customization
 - Absolutely everything can be customized and modified - nothing is required

# Upcoming features

 - Stateless database migrations via [mygrations](https://github.com/cmancone/mygrations)
 - User-configurable rules engine
 - Auto generated API documentation

# Not Included

 - Built in webserver (That's what lambdas, queue managers, and simple WSGI servers are for)
 - More advanced routing options (microservices probably don't need much routing, and load balancers can handle the rest)
 - Log handling - that's what cloudwatch and log aggregators are for
 - Views, templates, content management
 - Anything that even remotely resembles a front end
 - Basically anything not listed in the "Inside the Box" section above
