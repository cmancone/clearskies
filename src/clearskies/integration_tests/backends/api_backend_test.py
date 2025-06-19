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
                UserRepo, foreign_column_name="login", readable_child_column_names=["id", "full_name", "html_url"]
            )

        def fetch_user(users: User, user_repos: UserRepo):
            # If we execute this models query:
            some_repos = (
                user_repos.where("login=cmancone")
                .sort_by("created", "desc")
                .where("type=owner")
                .pagination(page=2)
                .limit(5)
            )
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
        response_2.json = MagicMock(
            return_value={
                "id": "1",
                "login": "cmancone",
                "full_name": "Conor Mancone",
                "html_url": "https://clearskies.info",
            }
        )
        response_2.ok = True
        response_2.status_code = 200
        response_3 = MagicMock()
        response_3.json = MagicMock(
            return_value=[
                {"id": "2", "full_name": "repo_1", "html_url": "https://repo.com"},
                {"id": "3", "full_name": "repo_2", "html_url": "https://another.com"},
            ]
        )
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
                {"id": 3, "full_name": "repo_2", "html_url": "https://another.com"},
            ],
        }

    def test_overview_list(self):
        class User(clearskies.Model):
            id_column_name = "login"
            backend = clearskies.backends.ApiBackend(
                pagination_parameter_name="since",
                base_url="https://api.github.com",
                limit_parameter_name="per_page",
            )

            id = clearskies.columns.Integer()
            login = clearskies.columns.String()
            gravatar_id = clearskies.columns.String()
            avatar_url = clearskies.columns.String()
            html_url = clearskies.columns.String()
            repos_url = clearskies.columns.String()

        requests = MagicMock()
        response = MagicMock()
        response.ok = True
        response.headers = {
            "link": (
                ' <https://api.github.com/users?per_page=5&since=5>; rel="next", <https://api.github.com/users{?since}>; rel="first"'
            )
        }
        response.json = MagicMock(
            return_value=[
                {"id": "4", "login": "eijerei", "html_url": "https://github.com/eijerei"},
                {"id": "5", "login": "qwerty", "html_url": "https://github.com/qwerty"},
            ]
        )
        requests.request = MagicMock(return_value=response)

        context = Context(
            clearskies.endpoints.List(
                model_class=User,
                readable_column_names=["id", "login", "html_url"],
                sortable_column_names=["id"],
                default_sort_column_name=None,
                default_limit=10,
            ),
            classes=[User],
            bindings={"requests": requests},
        )

        (status_code, response, response_headers) = context()
        assert status_code == 200
        assert response["data"] == [
            {"id": 4, "login": "eijerei", "html_url": "https://github.com/eijerei"},
            {"id": 5, "login": "qwerty", "html_url": "https://github.com/qwerty"},
        ]
        assert response["pagination"] == {
            "limit": 10,
            "next_page": {
                "since": "5",
            },
            "number_results": None,
        }

    def test_casing(self):
        class User(clearskies.Model):
            id_column_name = "login"
            backend = clearskies.backends.ApiBackend(
                base_url="https://api.github.com",
                limit_parameter_name="per_page",
                pagination_parameter_name="since",
                model_casing="TitleCase",
                api_casing="snake_case",
            )

            Id = clearskies.columns.Integer()
            Login = clearskies.columns.String()
            GravatarId = clearskies.columns.String()
            AvatarUrl = clearskies.columns.String()
            HtmlUrl = clearskies.columns.String()
            ReposUrl = clearskies.columns.String()

        requests = MagicMock()
        response = MagicMock()
        response.ok = True
        response.headers = {
            "link": (
                ' <https://api.github.com/users?per_page=5&since=5>; rel="next", <https://api.github.com/users{?since}>; rel="first"'
            )
        }
        response.json = MagicMock(
            return_value=[
                {
                    "id": "4",
                    "login": "eijerei",
                    "avatar_url": "https://avatar.com",
                    "html_url": "https://github.com/eijerei",
                    "repos_url": "https://repos.com",
                },
            ]
        )
        requests.request = MagicMock(return_value=response)

        context = Context(
            clearskies.endpoints.List(
                model_class=User,
                readable_column_names=["Login", "AvatarUrl", "HtmlUrl", "ReposUrl"],
                sortable_column_names=["Id"],
                default_sort_column_name=None,
                default_limit=2,
                internal_casing="TitleCase",
                external_casing="TitleCase",
            ),
            classes=[User],
            bindings={"requests": requests},
        )

        (status_code, response, response_headers) = context()
        assert status_code == 200
        assert response["Status"] == "Success"
        assert response["Data"] == [
            {
                "Login": "eijerei",
                "AvatarUrl": "https://avatar.com",
                "HtmlUrl": "https://github.com/eijerei",
                "ReposUrl": "https://repos.com",
            },
        ]

    def test_map(self):
        class User(clearskies.Model):
            id_column_name = "login"
            backend = clearskies.backends.ApiBackend(
                base_url="https://api.github.com",
                limit_parameter_name="per_page",
                pagination_parameter_name="since",
                api_to_model_map={"html_url": "profile_url"},
            )

            id = clearskies.columns.Integer()
            login = clearskies.columns.String()
            profile_url = clearskies.columns.String()

        requests = MagicMock()
        response = MagicMock()
        response.ok = True
        response.headers = {
            "link": (
                ' <https://api.github.com/users?per_page=5&since=5>; rel="next", <https://api.github.com/users{?since}>; rel="first"'
            )
        }
        response.json = MagicMock(
            return_value=[
                {
                    "id": "4",
                    "login": "eijerei",
                    "avatar_url": "https://avatar.com",
                    "html_url": "https://github.com/eijerei",
                    "repos_url": "https://repos.com",
                },
            ]
        )
        requests.request = MagicMock(return_value=response)

        context = Context(
            clearskies.endpoints.List(
                model_class=User,
                readable_column_names=["login", "profile_url"],
                sortable_column_names=["id"],
                default_sort_column_name=None,
                default_limit=2,
            ),
            classes=[User],
            bindings={"requests": requests},
        )

        (status_code, response, response_headers) = context()
        assert status_code == 200
        assert response["status"] == "success"
        assert response["data"] == [
            {"login": "eijerei", "profile_url": "https://github.com/eijerei"},
        ]
