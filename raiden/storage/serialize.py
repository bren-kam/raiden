import importlib
import json
from raiden.utils.serialization import ReferenceCache


class RaidenJSONEncoder(json.JSONEncoder):
    """ A custom JSON encoder to provide convenience
    of recursive instance encoding. """
    def default(self, obj):
        """
        If an object has `to_dict` method, call that method.
        """
        if hasattr(obj, 'to_dict'):
            result = obj.to_dict()
            result['_type'] = f'{obj.__module__}.{obj.__class__.__name__}'
            result['_version'] = 0
            return result
        return super().default(obj)


class RaidenJSONDecoder(json.JSONDecoder):
    """ A custom JSON decoder which facilitates
    specific object type invocation to restore
    it's state.
    """

    # Maintain a global cache instance
    # which lives across different decoder instances
    _ref_cache = ReferenceCache()

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, data):
        """
        detects the type of a JSON object, imports the class
        of that type and calls `to_dict`
        """
        if '_type' in data:
            obj = None
            obj_type = data['_type']

            klass = self._import_type(obj_type)
            if hasattr(klass, 'from_dict'):
                obj = klass.from_dict(data)

            candidate = self._ref_cache.get(obj_type, obj)
            if not candidate:
                self._ref_cache.add(obj_type, obj)
                return obj
            return candidate

        return data

    def _import_type(self, type_name):
        *module_name, klass_name = type_name.split('.')
        module_name = '.'.join(module_name)

        try:
            module = importlib.import_module(module_name, None)
        except ModuleNotFoundError:
            raise TypeError(f'Module {module_name} does not exist')

        if not hasattr(module, klass_name):
            raise TypeError(f'Could not find {module_name}.{klass_name}')
        klass = getattr(module, klass_name)
        return klass


class JSONSerializer:
    @staticmethod
    def serialize(obj):
        return json.dumps(obj, cls=RaidenJSONEncoder)

    @staticmethod
    def deserialize(data):
        return json.loads(data, cls=RaidenJSONDecoder)
