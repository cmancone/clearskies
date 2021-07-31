# Installation

Install clearskies via pip:

```
pip3 install clear-skies
```

# Dependencies

In general, clearskies aims to minimize external depenedncies to help keep builds small.  This doesn't mean that it doesn't have any dependencies: just that they aren't always required and so they aren't installed by default.  Here are some additional dependencies used by clearskies, and what features they are required for:

| Dependency  | Used by                                     |
|-------------|---------------------------------------------|
| requests    | API Backend, anything making an API request |
| pymysql     | Cursor Backend                              |
| python-jose | JWT Authentication                          |

If you try to use one of the above features but haven't installed the required dependency, things will break.  Unless I hear complaints otherwise, I don't intend to ever have these dependencies installed automatically with clearskies.  This is mainly because there are plenty of clearskies use cases where the above dependencies will not be needed, so I don't want to force people to install them.

Of course, this only covers the dependencies for core clearskies functionality.  Since clearskies focuses on adding features via sideloading, additional functionality is typically packaged up through separate installable modules, which come with their own required dependencies.

Next: [But Why?](./2_but_why.md)
