# Falcon JSON IO

Validate HTTP request and response body by defining acceptable values with JSON
schema.  For use with the [Falcon web framework](http://falconframework.org/).

Define your request body schema, and your endpoint is only called if the
request matches your specification.  Otherwise, an error is returned to the
caller.

Define your response body schema, and your response is validated before
returning to the sender.  A response that does not match the specification will
return a 500 error instead.

Retrieve your request JSON using req.context['doc'].

Set your JSON response in req.context['result'].

## Using the middleware

Enabled the middleware:

```
app = falcon.API(
    middleware=[
        falconjsonio.middleware.RequireJSON(),
        falconjsonio.middleware.JSONTranslator(),
    ],
)
```

Define your requirements:

```
from falconjsonio.schema import request_schema, response_schema

people_post_request_schema = {
    'type':       'object',
    'properties': {
        'title':  {'type': 'string'},
        'name':   {'type': 'string'},
        'dob':    {'type': 'date-time'},
        'email':  {'type': 'email'},
    },
    'required': ['name', 'dob'],
}
people_post_response_schema = {
    'oneOf': [
        {
            'type':       'object',
            'properties': {
                'href': {'type': uri'},
            },
            'required': ['uri'],
        },
        {
            'type':       'object',
            'properties': {
                'error': {'type': 'string'},
            },
            'required': ['error'],
        },
    ],
}

# ...

class People(object):
    @response_schema(people_get_response_schema)
    def on_get(self, req, resp):
        # Put your JSON response here:
        req.context['result'] = {'some': 'json'}

    @request_schema(people_post_request_schema)
    @response_schema(people_post_response_schema)
    def on_post(self, req, resp):
        # JSON request supplied here:
        form = req.context['doc']
        # Put your JSON response here:
        req.context['result'] = {'some': 'json'}
```

Hook the endpoint in, of course:

```
app.add_route('/people', People())
```

## Quick start for contributing

```
virtualenv -p `which python3` virtualenv
source virtualenv/bin/activate
pip install -r requirements.txt
pip install -r dev_requirements.txt
nosetests
```
