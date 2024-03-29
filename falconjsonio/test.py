import falconjsonio.middleware, falconjsonio.schema

import falcon, falcon.testing
import json
import jsonschema
import logging
import unittest


class NonJSONResource(object):
    def __init__(self):
        self.received = None

    def on_post(self, req, resp):
        self.received   = req.stream.read()
        resp.status     = falcon.HTTP_201
        resp.body       = self.received
        resp.set_header('Content-Type', req.content_type)

class SchemalessJSONResource(object):
    def __init__(self):
        self.received = None

    def on_post(self, req, resp):
        self.received           = req.context['doc']
        resp.status             = falcon.HTTP_201
        req.context['result']   = self.received
        resp.set_header('Content-Type', req.content_type)

class GoodResource(object):
    def __init__(self):
        self.received = None

    @falconjsonio.schema.request_schema({
        'type': 'object',
        'properties': {
            'email':    {'type': 'string'},
            'password': {'type': 'string'},
        },
        'required': ['email', 'password'],
    })
    @falconjsonio.schema.response_schema({
        'type': 'object',
        'properties': {
            'email': {'type': 'string'},
        },
        'required': ['email'],
    })
    def on_post(self, req, resp):
        self.received = req.context['doc']
        resp.status = falcon.HTTP_201
        req.context['result'] = {'email': req.context['doc']['email']}

    @falconjsonio.schema.response_schema({
        'type': 'object',
        'properties': {
            'id': {'type': 'integer'},
        },
        'required': ['id'],
    })
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        req.context['result'] = {'id': 12345}

class GoodParentResource(object):
    def __init__(self):
        self.received = None

    def on_post(self, req, resp):
        self.received = req.context['doc']
        resp.status = falcon.HTTP_201
        req.context['result'] = {'email': req.context['doc']['email']}

@falconjsonio.schema.request_schema(schema={
    'type': 'object',
    'properties': {
        'email':    {'type': 'string'},
        'password': {'type': 'string'},
    },
    'required': ['email', 'password'],
}, method_name='on_post')
@falconjsonio.schema.response_schema(schema={
    'type': 'object',
    'properties': {
        'email': {'type': 'string'},
    },
    'required': ['email'],
}, method_name='on_post')
class GoodChildResource(GoodParentResource):
    pass

class BadParentResource(object):
    def on_post(self, req, resp):
        self.received = req.context['doc']
        resp.status = falcon.HTTP_201
        req.context['result'] = {'this': 'does not conform'}

@falconjsonio.schema.request_schema(schema={
    'type': 'object',
    'properties': {
        'email':    {'type': 'string'},
        'password': {'type': 'string'},
    },
    'required': ['email', 'password'],
}, method_name='on_post')
@falconjsonio.schema.response_schema(schema={
    'type': 'object',
    'properties': {
        'email': {'type': 'string'},
    },
    'required': ['email'],
}, method_name='on_post')
class BadChildResource(BadParentResource):
    pass

class BadResource(object):
    def __init__(self):
        self.received = None

    @falconjsonio.schema.request_schema({
        'type': 'object',
        'properties': {
            'email':    {'type': 'string'},
            'password': {'type': 'string'},
        },
        'required': ['email', 'password'],
    })
    @falconjsonio.schema.response_schema({
        'type': 'object',
        'properties': {
            'email': {'type': 'string'},
        },
        'required': ['email'],
    })
    def on_post(self, req, resp):
        self.received = req.context['doc']
        resp.status = falcon.HTTP_201
        req.context['result'] = {'this': 'does not conform'}

    @falconjsonio.schema.response_schema({
        'type': 'object',
        'properties': {
            'id': {'type': 'integer'},
        },
        'required': ['id'],
    })
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        req.context['result'] = {'this': 'does not conform'}

class CollectingHandler(logging.Handler):
    def __init__(self):
        super(CollectingHandler, self).__init__()
        self.logs = []
    def emit(self, record):
        self.logs.append(record)

format_checker = jsonschema.FormatChecker()

@format_checker.checks('allcaps', raises=ValueError)
def custom_format_validation(instance):
    return instance.isupper()

class StringFormatResource(object):

    @falconjsonio.schema.request_schema({
        'type': 'object',
        'properties': {
            'hostname':  {'format': 'hostname'},
            'ipv4':      {'format': 'ipv4'},
            'ipv6':      {'format': 'ipv6'},
            'email':     {'format': 'email'},
            'uri':       {'format': 'uri'},
            'date-time': {'format': 'date-time'},
            'date':      {'format': 'date'},
            'time':      {'format': 'time'},
            'regex':     {'format': 'regex'},
            'color':     {'format': 'color'},
            'allcaps':   {'format': 'allcaps'},
        }
    }, validator_kwargs=dict(format_checker=format_checker))
    def on_post(self, req, resp):
        resp.status = falcon.HTTP_201

class IOTest(unittest.TestCase):
    def setUp(self):
        super(IOTest, self).setUp()

        self.logger = logging.getLogger('TestLogger')
        self.handler = CollectingHandler()
        self.logger.handlers = []
        self.logger.addHandler(self.handler)

        self.app = falcon.API(
            middleware=[
                falconjsonio.middleware.RequireJSON(),
                falconjsonio.middleware.JSONTranslator(self.logger),
            ],
        )

        self.non_json_resource          = NonJSONResource()
        self.schemaless_json_resource   = SchemalessJSONResource()
        self.good_resource              = GoodResource()
        self.bad_resource               = BadResource()
        self.good_child_resource        = GoodChildResource()
        self.bad_child_resource         = BadChildResource()
        self.string_format_resource     = StringFormatResource()
        self.app.add_route('/non_json_response',        self.non_json_resource)
        self.app.add_route('/schemaless_json_response', self.schemaless_json_resource)
        self.app.add_route('/good_response',            self.good_resource)
        self.app.add_route('/bad_response',             self.bad_resource)
        self.app.add_route('/good_child_response',      self.good_child_resource)
        self.app.add_route('/bad_child_response',       self.bad_child_resource)
        self.app.add_route('/string_format_response',   self.string_format_resource)

        self.srmock = falcon.testing.StartResponseMock()

    def simulate_request(self, path, *args, **kwargs):
        env = falcon.testing.create_environ(path=path, **kwargs)
        return self.app(env, self.srmock)

    def test_no_accept(self):
        response, = self.simulate_request('/good_response', method='POST', body=json.dumps({}), headers={})
        self.assertEqual(self.srmock.status, '415 Unsupported Media Type')
        self.assertEqual((json.loads(response.decode('utf-8')))['title'], 'Unsupported media type')

    def test_unsupported_accept(self):
        response = self.simulate_request('/good_response', method='POST', body=json.dumps({}), headers={'Accept': 'text/html'})
        self.assertEqual(len(response), 0) # Unsupported media type, so we can't respond with a body
        self.assertEqual(self.srmock.status, '406 Not Acceptable')

    def test_no_content_type(self):
        response = self.simulate_request('/good_response', method='POST', body=json.dumps({}), headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '415 Unsupported Media Type')

    def test_unsupported_content_type(self):
        response = self.simulate_request('/good_response', method='POST', body=json.dumps({}), headers={'Accept': 'application/json', 'Content-Type': 'text/html'})
        self.assertEqual(self.srmock.status, '415 Unsupported Media Type')

    def test_non_json_endpoint(self):
        response = self.simulate_request('/non_json_response', method='POST', body='Hello this is some text', headers={'Accept': 'application/json, text/plain', 'Content-Type': 'text/plain'})
        self.assertEqual(self.srmock.status, '201 Created')
        self.assertEqual(response[0].decode('utf-8'), 'Hello this is some text')
        self.assertEqual(self.non_json_resource.received.decode('utf-8'), 'Hello this is some text')

    def test_schemaless_json_endpoint(self):
        response = self.simulate_request('/schemaless_json_response', method='POST', body=json.dumps({'hello': 'world'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.srmock.status, '201 Created')
        self.assertEqual(json.loads(response[0].decode('utf-8')), {'hello': 'world'})

    def test_post(self):
        response = self.simulate_request('/good_response', method='POST', body=json.dumps({'email': 'foo@example.com', 'password': 'hunter2'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.good_resource.received, {'email': 'foo@example.com', 'password': 'hunter2'})
        self.assertEqual(self.srmock.status, '201 Created')
        self.assertEqual(json.loads(response[0].decode('utf-8')), {'email': 'foo@example.com'})

    def test_nonexistent_method(self):
        response = self.simulate_request('/good_response', method='PUT', body=json.dumps({'email': 'foo@example.com', 'password': 'hunter2'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.srmock.status, '405 Method Not Allowed')

    def test_empty_post(self):
        response = self.simulate_request('/good_response', method='POST', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.srmock.status, '400 Bad Request')

    def test_nonconforming_post_request(self):
        response = self.simulate_request('/good_response', method='POST', body=json.dumps({'email': 'foo@example.com'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.good_resource.received, None)
        self.assertEqual(self.srmock.status, '400 Bad Request')
        self.assertEqual((json.loads(response[0].decode('utf-8')))['title'], 'Invalid request body')

    def test_nonconforming_post_response(self):
        response, = self.simulate_request('/bad_response', method='POST', body=json.dumps({'email': 'foo@example.com', 'password': 'hunter2'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.bad_resource.received, {'email': 'foo@example.com', 'password': 'hunter2'})
        self.assertEqual(self.srmock.status, '500 Internal Server Error')
        # Programming error is logged
        self.assertEqual(
            [self.handler.logs[0].message],
            ["""Blocking proposed response from being sent from falconjsonio.test.BadResource.on_post to client as it does not match the defined schema: 'email' is a required property

Failed validating 'required' in schema:
    {'properties': {'email': {'type': 'string'}},
     'required': ['email'],
     'type': 'object'}

On instance:
    {'this': 'does not conform'}"""]
        )

        self.assertEqual(json.loads(response.decode('utf-8')), {'title': 'Internal Server Error', 'description': 'Undisclosed'})

###
    def test_no_accept_inherited(self):
        response, = self.simulate_request('/good_child_response', method='POST', body=json.dumps({}), headers={})
        self.assertEqual(self.srmock.status, '415 Unsupported Media Type')
        self.assertEqual((json.loads(response.decode('utf-8')))['title'], 'Unsupported media type')

    def test_unsupported_accept_inherited(self):
        response = self.simulate_request('/good_child_response', method='POST', body=json.dumps({}), headers={'Accept': 'text/html'})
        self.assertEqual(len(response), 0) # Unsupported media type, so we can't respond with a body
        self.assertEqual(self.srmock.status, '406 Not Acceptable')

    def test_no_content_type_inherited(self):
        response = self.simulate_request('/good_child_response', method='POST', body=json.dumps({}), headers={'Accept': 'application/json'})
        self.assertEqual(self.srmock.status, '415 Unsupported Media Type')

    def test_unsupported_content_type_inherited(self):
        response = self.simulate_request('/good_child_response', method='POST', body=json.dumps({}), headers={'Accept': 'application/json', 'Content-Type': 'text/html'})
        self.assertEqual(self.srmock.status, '415 Unsupported Media Type')

    def test_post_inherited(self):
        response = self.simulate_request('/good_child_response', method='POST', body=json.dumps({'email': 'foo@example.com', 'password': 'hunter2'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.good_child_resource.received, {'email': 'foo@example.com', 'password': 'hunter2'})
        self.assertEqual(self.srmock.status, '201 Created')
        self.assertEqual(json.loads(response[0].decode('utf-8')), {'email': 'foo@example.com'})

    def test_nonconforming_post_request_inherited(self):
        response = self.simulate_request('/good_child_response', method='POST', body=json.dumps({'email': 'foo@example.com'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.good_child_resource.received, None)
        self.assertEqual(self.srmock.status, '400 Bad Request')
        self.assertEqual((json.loads(response[0].decode('utf-8')))['title'], 'Invalid request body')

    def test_nonconforming_post_response_inherited(self):
        response, = self.simulate_request('/bad_child_response', method='POST', body=json.dumps({'email': 'foo@example.com', 'password': 'hunter2'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.bad_child_resource.received, {'email': 'foo@example.com', 'password': 'hunter2'})
        self.assertEqual(self.srmock.status, '500 Internal Server Error')
        # Programming error is logged
        self.assertEqual(
            [self.handler.logs[0].message],
            ["""Blocking proposed response from being sent from falconjsonio.test.BadChildResource.on_post to client as it does not match the defined schema: 'email' is a required property

Failed validating 'required' in schema:
    {'properties': {'email': {'type': 'string'}},
     'required': ['email'],
     'type': 'object'}

On instance:
    {'this': 'does not conform'}"""]
        )

        self.assertEqual(json.loads(response.decode('utf-8')), {'title': 'Internal Server Error', 'description': 'Undisclosed'})

    def test_invalid_class_request_schema_call(self):
        with self.assertRaises(falconjsonio.schema.SchemaDecoratorError):
            @falconjsonio.schema.request_schema({})
            class Foo(object):
                pass

        with self.assertRaises(falconjsonio.schema.SchemaDecoratorError):
            @falconjsonio.schema.response_schema({})
            class Foo(object):
                pass

    def test_conforming_string_formats(self):
        response = self.simulate_request('/string_format_response', method='POST', body=json.dumps(
            {
                'hostname': 'A.X.COM',
                'ipv4': '129.144.52.38',
                'ipv6': '::FFFF:129.144.52.38',
                'email': 'user@example.com',
                'uri': 'http://www.ietf.org/rfc/rfc2396.txt',
                'date-time': '2017-05-31T07:08:58Z',
                'date': '2017-05-31',
                'time': '07:03:33',
                'regex': r'\d+\.\d*',
                'color': '#daa520',
                'allcaps': 'ALLCAPS',
            }
        ), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.srmock.status, '201 Created', response)

    def test_non_conforming_string_format_builtin(self):
        self.simulate_request('/string_format_response', method='POST', body=json.dumps({'hostname': 'not a hostname'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.srmock.status, '400 Bad Request')

    def test_non_conforming_string_format_installed_rfc3987(self):
        self.simulate_request('/string_format_response', method='POST', body=json.dumps({'uri': 'not a uri'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.srmock.status, '400 Bad Request')

    def test_non_conforming_string_format_installed_strict_rfc3339(self):
        self.simulate_request('/string_format_response', method='POST', body=json.dumps({'date-time': 'not a date-time'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.srmock.status, '400 Bad Request')

    def test_non_conforming_string_format_installed_webcolors(self):
        self.simulate_request('/string_format_response', method='POST', body=json.dumps({'color': 'not a color'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.srmock.status, '400 Bad Request')

    def test_non_conforming_string_format_custom(self):
        self.simulate_request('/string_format_response', method='POST', body=json.dumps({'allcaps': 'not allcaps'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.srmock.status, '400 Bad Request')
