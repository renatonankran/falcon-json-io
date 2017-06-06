import jsonschema.validators
import inspect


class SchemaDecoratorError(Exception): pass


class _schema(object):
    def __init__(self, schema, method_name=None, validator_cls=None, validator_args=None, validator_kwargs=None):
        if validator_cls is None:
            validator_cls = jsonschema.validators.validator_for(schema)
        if validator_args is None:
            validator_args = []
        if validator_kwargs is None:
            validator_kwargs = {}

        validator_cls.check_schema(schema)
        self.validator      = validator_cls(schema, *validator_args, **validator_kwargs)
        self.method_name    = method_name


class request_schema(_schema):
    """
    Decorator to specify the JSON schema required for a request.
    """
    def __call__(self, klass_or_func):
        if inspect.isclass(klass_or_func):
            if self.method_name is None:
                raise SchemaDecoratorError("Parameter 'method_name' must be supplied when applying request_schema decorator to a class")
            if not hasattr(klass_or_func, '__request_schemas__'):
                klass_or_func.__request_schemas__ = {}
            klass_or_func.__request_schemas__[self.method_name] = self.validator
        else:
            klass_or_func.__request_schema__ = self.validator
        return klass_or_func


class response_schema(_schema):
    """
    Decorator to specify the JSON schema a response should conform to.
    """
    def __call__(self, klass_or_func):
        if inspect.isclass(klass_or_func):
            if self.method_name is None:
                raise SchemaDecoratorError("Parameter 'method_name' must be supplied when applying response_schema decorator to a class")
            if not hasattr(klass_or_func, '__response_schemas__'):
                klass_or_func.__response_schemas__ = {}
            klass_or_func.__response_schemas__[self.method_name] = self.validator
        else:
            klass_or_func.__response_schema__ = self.validator
        return klass_or_func
