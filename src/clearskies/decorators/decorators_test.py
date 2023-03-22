import clearskies
import unittest
@clearskies.decorators.return_raw_response()
@clearskies.decorators.get('users/{user_id}')
@clearskies.decorators.bindings(sup='hey')
@clearskies.decorators.public()
def example_callable(user_id, request_data, sup):
    return {
        "price": 27.50,
        'user_id': user_id,
        'sup': sup,
    }
class DecoratorsTest(unittest.TestCase):
    def test_simple(self):
        call_function = clearskies.contexts.test(example_callable)
        result = call_function(url='/users/5')
        self.assertEquals({
            'price': 27.50,
            'user_id': '5',
            'sup': 'hey',
        }, result[0])
