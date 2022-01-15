from .aws_lambda_api_gateway import AWSLambdaAPIGateway
class AWSHttpAPIGateway(AWSLambdaAPIGateway):
    def __init__(self, event, context):
        self._event = event
        self._context = context
        self._path = event.get('requestContext', {}).get('http', {}).get('path')
        self._request_method = event.get('requestContext', {}).get('http', {}).get('method').upper()
        self._query_parameters = event['queryStringParameters'] if event['queryStringParameters'] is not None else {}
        self._path_parameters = event['pathParameters']
        self._request_headers = {}
        for (key, value) in event['headers'].items():
            self._request_headers[key.lower()] = value
