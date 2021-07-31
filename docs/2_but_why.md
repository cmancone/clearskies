# But what's the point?

A key goal of clearskies is to make your business logic as simple as possible to design, write, test, and re-use.  It does this by promoting a "new" first-class citizen and demoting some others.  Namely, clearskies moves the focus away from models and controllers and shifts the focus to _columns_.

To understand the goal here, consider a (seemingly) simple example: the email address in a user record.  Here are some examples of business logic that might exist for smoething as simple as an email address for a user:

1. The email address is required
2. The email address must be a valid email address
3. The email address must be unique
4. The domain for the email address must match a list of whitelisted (or blacklisted) domains
5. Before the email address can be changed, a verification code must be sent to the new and old address
6. When the email address is changed, the user must be sent a security notice
7. When the email address is changed, an audit log must be updated

In many frameworks all these pieces of logic get scattered across countless files.  Some logic may end up in controllers (probably even different controllers if you have separate endpoints for users and admins), input validation is likely defined separately, triggering email notices probably lives in a model, etc...  Separating all this business logic into multiple locations makes it harder to understand the lifecycle of a user's email address, which means more bugs.

# The SRP

Really, this is all about looking at the [SRP](https://en.wikipedia.org/wiki/Single-responsibility_principle) from a different perspective.  A typical application of the SRP divides programs along _functional_ lines: input validation here, user notifications here, etc...  This ends up dividing up business logic.

Clearskies applies the SRP to business logic: everything related to the email address goes here, password logic goes there, etc (although it's obviously possible to share data between columns when required).  This makes it much easier to get a clear picture of the lifecycle of your data, and also helps identify logic bugs that might otherwise get missed.

Most importantly though, this makes it substantially easier to reuse business logic.  When the logic for a particular column all lives in one place, it doesn't matter if that column is updated by an end user, or an admin, or even an automated background process: the business rules are applied the same everywhere by default!

# Death to controllers!

One side effect of this is the death of controllers.  Not that controllers are bad guys - they just aren't necessary.  After all, when each column already knows how to validate user input, apply business logic, and update external systems, you don't really need a controller anyway (nor do you need models for much!).  Therefore, all you really need to do to set up an endpoint in clearskies is tell it what columns are available for reading and writing, and the rest takes care of itself.
