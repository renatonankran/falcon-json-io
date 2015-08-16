import falcon
import json
import jsonschema


class RequireJSON(object):
    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable('This API supports only JSON-encoded responses')
        if req.method in ('POST', 'PUT'):
            if req.content_type is None or 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType('This API supports only JSON-encoded requests')

class JSONTranslator(object):
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
        if resource is not None and req.method in ['POST', 'PUT']:
            schema = getattr(
                getattr(resource, {'POST': 'on_post', 'PUT': 'on_put'}[req.method]),
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

        schema = getattr(
                getattr(resource, {'POST': 'on_post', 'PUT': 'on_put', 'GET': 'on_get', 'DELETE': 'on_delete'}[req.method]),
            '__response_schema__',
            None
        )
        if schema is not None:
            try:
                jsonschema.validate(req.context['result'], schema)
            except jsonschema.exceptions.ValidationError as error:
                # TODO Log this so API developer can fix it
                raise falcon.HTTPInternalServerError(
                    'Invalid response body',
                    json.dumps({'error': str(error)})
                )
