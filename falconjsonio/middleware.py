import falcon
import json
import jsonschema
import logging


class _null_handler(logging.Handler):
    def emit(self, record):
        pass

class RequireJSON(object):
    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable('This API supports only JSON-encoded responses')
        if req.method in ('POST', 'PUT'):
            if req.content_type is None or 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType('This API supports only JSON-encoded requests')

class JSONTranslator(object):
    def __init__(self, logger=None):
        if logger is None:
            # Default to no logging if no logger provided
            logger = logging.getLogger(__name__)
            logger.addHandler(_null_handler())
        self.logger = logger

    def process_request(self, req, resp):
        if req.content_length in (None, 0):
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest(
                'Empty request body',
                'A valid JSON document is required'
            )

        try:
            req.context['doc'] = json.loads(body.decode('utf-8'))
        except (ValueError, UnicodeDecodeError) as error:
            raise falcon.HTTPBadRequest(
                'Malformed JSON',
                'Could not decode the request body.  The JSON was incorrect or not encoded as UTF-8'
            )

    def process_resource(self, req, resp, resource):
        if resource is not None and req.method in ['POST', 'PUT', 'PATCH']:
            schema = getattr(
                getattr(resource, {'POST': 'on_post', 'PUT': 'on_put', 'PATCH': 'on_patch'}[req.method]),
                '__request_schema__',
                None
            )
            if schema is not None:
                try:
                    jsonschema.validate(req.context['doc'], schema)
                except jsonschema.exceptions.ValidationError as error:
                    raise falcon.HTTPBadRequest(
                        'Invalid request body',
                        json.dumps({'error': str(error)})
                    )

    def process_response(self, req, resp, resource):
        if 'result' not in req.context:
            return

        resp.body = json.dumps(req.context['result'])

        try:
            method_name = {'POST': 'on_post', 'PUT': 'on_put', 'PATCH': 'on_patch', 'GET': 'on_get', 'DELETE': 'on_delete'}[req.method]
        except KeyError:
            return

        schema = getattr(
            getattr(resource, method_name),
            '__response_schema__',
            None
        )
        if schema is None:
            return

        try:
            jsonschema.validate(req.context['result'], schema)
        except jsonschema.exceptions.ValidationError as error:
            self.logger.error('Blocking proposed response from being sent from {0}.{1}.{2} to client as it does not match the defined schema: {3}'.format(resource.__module__, resource.__class__.__name__, method_name, str(error)))
            raise falcon.HTTPInternalServerError('Internal Server Error', 'Undisclosed')
