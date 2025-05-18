import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context

class ManyToManyIdsWithDataTest(unittest.TestCase):
    def test_default(self):
        class ThingyWidgets(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            # these could also be belongs to relationships, but the pivot model
            # is rarely used directly, so I'm being lazy to avoid having to use
            # model references.
            thingy_id = clearskies.columns.String()
            widget_id = clearskies.columns.String()
            name = clearskies.columns.String()
            kind = clearskies.columns.String()

        class Thingy(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()

        class Widget(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            thingy_ids = clearskies.columns.ManyToManyIdsWithData(
                related_model_class=Thingy,
                pivot_model_class=ThingyWidgets,
                readable_pivot_column_names=["id", "thingy_id", "widget_id", "name", "kind"],
            )
            thingies = clearskies.columns.ManyToManyModels("thingy_ids")
            thingy_widgets = clearskies.columns.ManyToManyPivots("thingy_ids")

        def my_application(widgets: Widget, thingies: Thingy):
            thing_1 = thingies.create({"name": "Thing 1"})
            thing_2 = thingies.create({"name": "Thing 2"})
            thing_3 = thingies.create({"name": "Thing 3"})
            widget = widgets.create({
                "name": "Widget 1",
                "thingy_ids": [
                    {"thingy_id": thing_1.id, "name": "Widget Thing 1", "kind": "Special"},
                    {"thingy_id": thing_2.id, "name": "Widget Thing 2", "kind": "Also Special"},
                ],
            })

            return widget

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                my_application,
                model_class=Widget,
                return_records=True,
                readable_column_names=["id", "name", "thingy_widgets"],
            ),
            classes=[Widget, Thingy, ThingyWidgets],
        )
        (status_code, response_data, response_headers) = context()
        assert [record["name"] for record in response_data["data"]["thingy_widgets"]] == ["Widget Thing 1", "Widget Thing 2"]
