from .merge import merge


def delete(path, **kwargs):
    def wrap_in_application(function):
        kwargs["path"] = path
        return merge(function, **{**kwargs, "methods": "DELETE"})

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
