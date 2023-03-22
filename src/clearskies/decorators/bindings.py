from .merge import merge
def bindings(**kwargs):
    def wrap_in_application(function):
        return merge(function, bindings=kwargs)

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
