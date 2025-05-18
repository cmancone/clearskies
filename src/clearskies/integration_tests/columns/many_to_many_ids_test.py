import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context

class ManyToManyIdsTest(unittest.TestCase):
    def test_default(self):
        class ThingyToWidget(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            # these could also be belongs to relationships, but the pivot model
            # is rarely used directly, so I'm being lazy to avoid having to use
            # model references.
            thingy_id = clearskies.columns.String()
            widget_id = clearskies.columns.String()

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
            thingy_ids = clearskies.columns.ManyToManyIds(
                related_model_class=Thingy,
                pivot_model_class=ThingyToWidget,
            )
            thingies = clearskies.columns.ManyToManyModels("thingy_ids")


        def my_application(widgets: Widget, thingies: Thingy):
            thing_1 = thingies.create({"name": "Thing 1"})
            thing_2 = thingies.create({"name": "Thing 2"})
            thing_3 = thingies.create({"name": "Thing 3"})
            widget = widgets.create({
                "name": "Widget 1",
                "thingy_ids": [thing_1.id, thing_2.id],
            })

            # remove an item by saving without it's id in place
            widget.save({"thingy_ids": [thing.id for thing in widget.thingies if thing.id != thing_1.id]})

            # add an item by saving and adding the new id
            widget.save({"thingy_ids": [*widget.thingy_ids, thing_3.id]})

            return widget.thingies

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                my_application,
                model_class=Thingy,
                return_records=True,
                readable_column_names=["id", "name"],
            ),
            classes=[Widget, Thingy, ThingyToWidget],
        )
        (status_code, response_data, response_headers) = context()

        assert [record["name"] for record in response_data["data"]] == ["Thing 2", "Thing 3"]
