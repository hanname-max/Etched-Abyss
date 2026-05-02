from typing import Any, Dict, Type, TypeVar, Optional

T = TypeVar('T')


class ServiceLocator:
    _instance: Optional['ServiceLocator'] = None
    _services: Dict[Type[Any], Any] = {}

    def __new__(cls) -> 'ServiceLocator':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None
        cls._services = {}

    def register_service(self, service_type: Type[T], instance: T) -> None:
        if service_type in self._services:
            raise ValueError(f"Service of type {service_type.__name__} is already registered")
        if not isinstance(instance, service_type):
            raise TypeError(f"Instance must be of type {service_type.__name__}")
        self._services[service_type] = instance

    def get_service(self, service_type: Type[T]) -> T:
        if service_type not in self._services:
            raise KeyError(f"Service of type {service_type.__name__} is not registered")
        return self._services[service_type]

    def try_get_service(self, service_type: Type[T]) -> Optional[T]:
        return self._services.get(service_type)

    def is_registered(self, service_type: Type[Any]) -> bool:
        return service_type in self._services

    def unregister_service(self, service_type: Type[Any]) -> None:
        if service_type in self._services:
            del self._services[service_type]

    def clear_all(self) -> None:
        self._services.clear()


def register_service(service_type: Type[T], instance: T) -> None:
    locator = ServiceLocator()
    locator.register_service(service_type, instance)


def get_service(service_type: Type[T]) -> T:
    locator = ServiceLocator()
    return locator.get_service(service_type)


def try_get_service(service_type: Type[T]) -> Optional[T]:
    locator = ServiceLocator()
    return locator.try_get_service(service_type)


def is_service_registered(service_type: Type[Any]) -> bool:
    locator = ServiceLocator()
    return locator.is_registered(service_type)
