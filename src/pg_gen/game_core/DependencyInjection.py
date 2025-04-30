from typing import Any


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

    def try_inject[T](self, service_type: type[T]) -> T | None:
        if service_type in self._lookup:
            return self._lookup[service_type]

        if hasattr(service_type, "__singleton_service__"):
            instance = service_type()
            self.register(service_type, instance)
            return instance

        return None

    def inject[T](self, service_type: type[T]) -> T:
        service = self.try_inject(service_type)
        if service is not None:
            return service

        raise KeyError(f"Cannot find service {service_type}")

    def __init__(self):
        self._lookup: dict[type, Any] = {}
        pass
