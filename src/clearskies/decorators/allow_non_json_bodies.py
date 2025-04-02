from .merge import merge


def allow_non_json_bodies():
    def wrap_in_application(function):
        return merge(function, allow_non_json_bodies=True)

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
