from abc import ABC
class Secrets:
    def create(self, path, value):
        raise NotImplementedError(
            "It looks like you tried to use the secret system in clearskies, but didn't specify a secret manager."
        )

    def get(self, path, silent_if_not_found=False):
        raise NotImplementedError(
            "It looks like you tried to use the secret system in clearskies, but didn't specify a secret manager."
        )

    def get_dynamic_secret(self, path):
        raise NotImplementedError(
            "It looks like you tried to use the secret system in clearskies, but didn't specify a secret manager."
        )

    def list_secrets(self, path):
        raise NotImplementedError(
            "It looks like you tried to use the secret system in clearskies, but didn't specify a secret manager."
        )

    def update(self, path, value):
        raise NotImplementedError(
            "It looks like you tried to use the secret system in clearskies, but didn't specify a secret manager."
        )

    def upsert(self, path, value):
        raise NotImplementedError(
            "It looks like you tried to use the secret system in clearskies, but didn't specify a secret manager."
        )
