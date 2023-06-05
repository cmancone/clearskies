from .merge import merge
def binding_classes(*args):
    def wrap_in_application(function):
        return merge(function, binding_classes=args)

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
