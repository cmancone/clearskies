import datetime
import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context


class TimestampTest(unittest.TestCase):
    def test_default(self):
        class Pet(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            last_fed = clearskies.columns.Timestamp()

        def demo_timestamp(utcnow: datetime.datetime, pets: Pet) -> dict[str, str | int]:
            pet = pets.create(
                {
                    "name": "Spot",
                    "last_fed": utcnow,
                }
            )
            return {
                "last_fed": pet.last_fed.isoformat(),
                "raw_data": pet.get_raw_data()["last_fed"],
            }

        utcnow = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                demo_timestamp,
            ),
            classes=[Pet],
            utcnow=utcnow,
        )
        (status_code, response_data, response_header) = context()

        assert response_data["data"]["last_fed"] == utcnow.isoformat()
        assert response_data["data"]["raw_data"] == utcnow.timestamp()
