from .string import String


class CreatedByRoutingData(String):
    required_configs = [
        "routing_data_name",
    ]

    def __init__(self, di):
        super().__init__(di)

    @property
    def is_writeable(self):
        return False

    def pre_save(self, data, model):
        if model.exists:
            return data

        input_output = self.di.build("input_output", cache=True)
        return {
            **data,
            self.name: input_output.get_request_header(self.config("routing_data_name")),
        }
