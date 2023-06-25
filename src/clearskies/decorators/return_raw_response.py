from .merge import merge


def return_raw_response():
    def wrap_in_application(function):
        return merge(function, return_raw_response=True)

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
