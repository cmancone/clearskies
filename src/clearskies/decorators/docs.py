from .merge import merge
def docs(doc_description=None, doc_model_name=None, doc_response_data_schema=None):
    def wrap_in_application(function):
        return merge(
            function,
            doc_description=doc_description,
            doc_model_name=doc_model_name,
            doc_response_data_schema=doc_response_data_schema
        )

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
