# Backends

The backend (i.e, the place where data is loaded from and persisted to) is very flexible in clearskies.  While clearskies defaults to using an SQL database, this can be changed from one model to another or overridden at run time.

The main "kinds" of backends currently available are the:

[Cursor Backend](#cursor-backend), which persists data to a MySQL/MariaDB database via [PyMySQL](https://pypi.org/project/PyMySQL/)
[Memory Backend](#memory-backend), which stores data locally.  This is useful for working with temporary data or when running test suites.
[API Backend](#api-backend), which is used to normalize API interactions as well as to automate integrations with APIs powered by clearskies

# Cursor Backend

### Overview

### Working with the Cursor Backend

# Memory Backend

### Overview

### Working with the Memory Backend

# API Backend

### Overview

### Working with the API Backend
