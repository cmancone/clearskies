class Authorization:
    def gate(self, authorization_data, input_output):
        """
        Return True/False to denote if the given user, as represented by the authorization data, should be allowed access.

        Raise clearskies.exceptions.ClientError if you want to raise a specific error message.
        """
        return True

    def filter_model(self, model, authorization_data, input_output):
        """Return a models object with additional filters applied to account for authorization needs."""
        return model
