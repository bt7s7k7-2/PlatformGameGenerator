from typing import Any, Dict


class DependencyInjection:

    def register[T](self, service_type: type[T], value: T):
        if service_type in self._lookup:
            raise ValueError(f"Duplicate registration for {service_type}")

        self._lookup[service_type] = value
        pass

    def unregister[T](self, service_type: type[T], value: T):
        if not service_type in self._lookup:
            raise ValueError(f"Tried to unregister {service_type}, but this service was never registered")

        prev = self._lookup[service_type]
        if prev is not value:
            raise ValueError(f"Tried to unregister {service_type}, but the registered service is different")

        self._lookup.pop(service_type)
        pass

    def inject[T](self, service_type: type[T]) -> T:
        if service_type in self._lookup:
            return self._lookup[service_type]

        if hasattr(service_type, "__singleton_service__"):
            instance = service_type()
            self.register(service_type, instance)
            return instance

        raise KeyError(f"Cannot find service {service_type}")

    def __init__(self):
        self._lookup: Dict[type, Any] = {}
        pass
