from .merge import merge


def create(path, **kwargs):
    def wrap_in_application(function):
        kwargs["path"] = path
        return merge(function, **{**kwargs, "methods": "CREATE"})

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
