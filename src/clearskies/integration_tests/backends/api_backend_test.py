import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context

class ApiBackendTest(unittest.TestCase):
    def test_overview(self):
        class GithubPublicBackend(clearskies.backends.ApiBackend):
            def __init__(
                self,
                pagination_parameter_name: str = "since",
            ):
                self.base_url = "https://api.github.com"
                self.limit_parameter_name = "per_page"
                self.pagination_parameter_name = pagination_parameter_name
                self.finalize_and_validate_configuration()

        class UserRepo(clearskies.Model):
            id_column_name = "full_name"
            backend = GithubPublicBackend(pagination_parameter_name="page")

            @classmethod
            def destination_name(cls) -> str:
                return "users/:login/repos"

            id = clearskies.columns.Integer()
            full_name = clearskies.columns.String()
            type = clearskies.columns.Select(["all", "owner", "member"])
            url = clearskies.columns.String()
            html_url = clearskies.columns.String()
            created_at = clearskies.columns.Datetime()
            updated_at = clearskies.columns.Datetime()
            login = clearskies.columns.String(is_searchable=True, is_readable=False)
            updated = clearskies.columns.Datetime(is_searchable=False, is_readable=False, is_writeable=False)
            created = clearskies.columns.Datetime(is_searchable=False, is_readable=False, is_writeable=False)

        class User(clearskies.Model):
            id_column_name = "login"
            backend = GithubPublicBackend()

            id = clearskies.columns.Integer()
            login = clearskies.columns.String()
            gravatar_id = clearskies.columns.String()
            avatar_url = clearskies.columns.String()
            html_url = clearskies.columns.String()
            repos_url = clearskies.columns.String()

            repos = clearskies.columns.HasMany(
                UserRepo,
                foreign_column_name="login",
                readable_child_columns=["id", "full_name", "html_url"]
            )

        def fetch_user(users: User, user_repos: UserRepo):
            # If we execute this models query:
            some_repos = user_repos.where("login=cmancone").sort_by("created", "desc").where("type=owner").pagination(page=2).limit(5)
            # the API backend will fetch this url:
            # https://api.github.com/users/cmancone/repos?type=owner&sort=created&direction=desc&per_page=5&page=2
            # and we can use the results like always
            repo_names = [repo.full_name for repo in some_repos]

            # For the below case, the backend will fetch this url:
            # https://api.github.com/users/cmancone
            # in addition, the readable column names on the callable endpoint includes "repos", which references our has_many
            # column.  This means that when converting the user model to JSON, it will also grab a page of repositories for that user.
            # To do that, it will fetch this URL:
            # https://api.github.com/users/cmancone/repos
            return users.find("login=cmancone")

        requests = MagicMock()
        requests.request = MagicMock()
        response_1 = MagicMock()
        response_1.json = MagicMock(return_value=[])
        response_1.ok = True
        response_1.status_code = 200
        response_2 = MagicMock()
        response_2.json = MagicMock(return_value={"id":"1","login":"cmancone","full_name":"Conor Mancone", "html_url": "https://clearskies.info"})
        response_2.ok = True
        response_2.status_code = 200
        response_3 = MagicMock()
        response_3.json = MagicMock(return_value=[{"id":"2", "full_name":"repo_1", "html_url":"https://repo.com"},{"id":"3", "full_name": "repo_2", "html_url":"https://another.com"}])
        requests.request.side_effect = [response_1, response_2, response_3]
        context = Context(
            clearskies.endpoints.Callable(
                fetch_user,
                model_class=User,
                readable_column_names=["id", "login", "html_url", "repos"],
            ),
            classes=[User, UserRepo],
            bindings={"requests": requests},
        )
        (status_code, response, response_headers) = context()
        assert status_code == 200
        assert response["data"] == {
            "id": 1,
            "login": "cmancone",
            "html_url": "https://clearskies.info",
            "repos": [
                {"id": 2, "full_name": "repo_1", "html_url": "https://repo.com"},
                {"id": 3, "full_name": "repo_2", "html_url":"https://another.com"},
            ]
        }
