import unittest
import datetime

import clearskies
from clearskies.contexts import Context
from clearskies.validators import Required, Unique
from clearskies import columns

class EndpointGroupTest(unittest.TestCase):
    def test_overview(self):
        class Company(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = columns.Uuid()
            name = columns.String(validators=[
                Required(),
                Unique(),
            ])

        class User(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = columns.Uuid()
            name = columns.String(validators=[Required()])
            username = columns.String(validators=[
                Required(),
                Unique(),
            ])
            age = columns.Integer(validators=[Required()])
            created_at = columns.Created()
            updated_at = columns.Updated()
            company_id = columns.BelongsToId(
                Company,
                readable_parent_columns=["id", "name"],
                validators=[Required()],
            )
            company = columns.BelongsToModel("company_id")


        readable_user_column_names = ['id', 'name', 'username', 'age', 'created_at', 'updated_at', 'company']
        writeable_user_column_names = ['name', 'username', 'age', 'company_id']
        users_api = clearskies.EndpointGroup(
            [
                clearskies.endpoints.Update(
                    model_class=User,
                    url='/:id',
                    readable_column_names=readable_user_column_names,
                    writeable_column_names=writeable_user_column_names,
                ),
                clearskies.endpoints.Delete(
                    model_class=User,
                    url='/:id',
                ),
                clearskies.endpoints.Get(
                    model_class=User,
                    url='/:id',
                    readable_column_names=readable_user_column_names,
                ),
                clearskies.endpoints.Create(
                    model_class=User,
                    readable_column_names=readable_user_column_names,
                    writeable_column_names=writeable_user_column_names,
                ),
                clearskies.endpoints.SimpleSearch(
                    model_class=User,
                    readable_column_names=readable_user_column_names,
                    sortable_column_names=readable_user_column_names,
                    searchable_column_names=readable_user_column_names,
                    default_sort_column_name="name",
                )
            ],
            url='users',
        )

        readable_company_column_names = ['id', 'name']
        writeable_company_column_names = ['name']
        companies_api = clearskies.EndpointGroup(
            [
                clearskies.endpoints.Update(
                    model_class=Company,
                    url='/:id',
                    readable_column_names=readable_company_column_names,
                    writeable_column_names=writeable_company_column_names,
                ),
                clearskies.endpoints.Delete(
                    model_class=Company,
                    url='/:id',
                ),
                clearskies.endpoints.Get(
                    model_class=Company,
                    url='/:id',
                    readable_column_names=readable_company_column_names,
                ),
                clearskies.endpoints.Create(
                    model_class=Company,
                    readable_column_names=readable_company_column_names,
                    writeable_column_names=writeable_company_column_names,
                ),
                clearskies.endpoints.SimpleSearch(
                    model_class=Company,
                    readable_column_names=readable_company_column_names,
                    sortable_column_names=readable_company_column_names,
                    searchable_column_names=readable_company_column_names,
                    default_sort_column_name="name",
                )
            ],
            url='companies'
        )

        context = clearskies.contexts.Context(clearskies.EndpointGroup([users_api, companies_api]))

        (status, response_data, response_headers) = context(
            url="/companies",
            request_method="POST",
            body={"name": "Box Store"},
        )
        assert response_data["data"]["name"] == "Box Store"
        company_id = response_data["data"]["id"]

        (status, response_data, response_headers) = context(
            url="/users",
            request_method="POST",
            body={"name": "Bob Brown", "username": "bobbrown", "age": 25, "company_id": company_id},
        )
        assert response_data["data"]["name"] == "Bob Brown"

        (status, response_data, response_headers) = context(
            url="/users",
            request_method="POST",
            body={"name": "Jane Doe", "username": "janedoe", "age": 32, "company_id": company_id},
        )
        assert response_data["data"]["name"] == "Jane Doe"

        (status, response_data, response_headers) = context(url="users")
        assert [user["username"] for user in response_data["data"]] == ["bobbrown", "janedoe"]
        assert [user["company"]["name"] for user in response_data["data"]] == ["Box Store", "Box Store"]
