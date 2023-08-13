from .string import String


class CreatedByAuthorizationData(String):
    required_configs = [
        "authorization_data_key_name",
    ]

    def __init__(self, di):
        super().__init__(di)

    @property
    def is_writeable(self):
        return False

    def pre_save(self, data, model):
        if model.exists:
            return data

        authorization_data = self.di.build("input_output", cache=True).get_authorization_data()
        # data comes last so that it can override the info in the authorization data.  This seems counter-intuitive,
        # but is important.  You would think that you *don't* want the data from the authorization data to be
        # overridden (since this is mainly used for logging), but the trouble is that there are a variety of use-cases
        # where the application must provide the audit data.  Examples include registration and login.  In these
        # cases, authorization data will be empty, and must be provided by the applicaiton.
        return {self.name: authorization_data.get(self.config("authorization_data_key_name"), "N/A"), **data}
