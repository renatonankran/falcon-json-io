class request_schema(object):
    """
    Decorator to specify the JSON schema required for a request.
    """
    def __init__(self, schema):
        self.schema = schema

    def __call__(self, func):
        func.__request_schema__ = self.schema
        return func

class response_schema(object):
    """
    Decorator to specify the JSON schema a response should conform to.
    """
    def __init__(self, schema):
        self.schema = schema

    def __call__(self, func):
        func.__response_schema__ = self.schema
        return func
