import falconjsonio.middleware, falconjsonio.schema

import falcon, falcon.testing
import json
import logging
import unittest


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

        self.good_resource  = GoodResource()
        self.bad_resource   = BadResource()
        self.app.add_route('/good_response', self.good_resource)
        self.app.add_route('/bad_response',  self.bad_resource)

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

    def test_post(self):
        response = self.simulate_request('/good_response', method='POST', body=json.dumps({'email': 'foo@example.com', 'password': 'hunter2'}), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(self.good_resource.received, {'email': 'foo@example.com', 'password': 'hunter2'})
        self.assertEqual(self.srmock.status, '201 Created')
        self.assertEqual(json.loads(response[0].decode('utf-8')), {'email': 'foo@example.com'})

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
