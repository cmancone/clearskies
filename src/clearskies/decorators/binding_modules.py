from .merge import merge
def binding_modules(*args):
    def wrap_in_application(function):
        return merge(function, binding_modules=args)

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
