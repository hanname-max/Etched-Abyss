import pytest
from CoreLogic import (
    ServiceLocator,
    register_service,
    get_service,
    try_get_service,
    is_service_registered
)


class TestService:
    def __init__(self, value: int = 0):
        self.value = value
    
    def get_value(self) -> int:
        return self.value


class AnotherService:
    def __init__(self, name: str = "default"):
        self.name = name


class TestServiceLocator:
    def setup_method(self):
        ServiceLocator.reset()
    
    def test_singleton_behavior(self):
        locator1 = ServiceLocator()
        locator2 = ServiceLocator()
        assert locator1 is locator2
    
    def test_register_and_get_service(self):
        service = TestService(42)
        register_service(TestService, service)
        
        retrieved = get_service(TestService)
        assert retrieved is service
        assert retrieved.get_value() == 42
    
    def test_get_nonexistent_service_raises_error(self):
        with pytest.raises(KeyError, match="Service of type TestService is not registered"):
            get_service(TestService)
    
    def test_try_get_service_returns_none_for_nonexistent(self):
        result = try_get_service(TestService)
        assert result is None
    
    def test_try_get_service_returns_instance_for_existent(self):
        service = TestService(100)
        register_service(TestService, service)
        
        result = try_get_service(TestService)
        assert result is service
        assert result.get_value() == 100
    
    def test_is_registered_returns_false_for_nonexistent(self):
        assert is_service_registered(TestService) is False
    
    def test_is_registered_returns_true_for_registered(self):
        service = TestService()
        register_service(TestService, service)
        
        assert is_service_registered(TestService) is True
    
    def test_register_duplicate_service_raises_error(self):
        service1 = TestService(1)
        service2 = TestService(2)
        
        register_service(TestService, service1)
        
        with pytest.raises(ValueError, match="Service of type TestService is already registered"):
            register_service(TestService, service2)
    
    def test_register_wrong_type_raises_error(self):
        wrong_service = AnotherService()
        
        with pytest.raises(TypeError, match="Instance must be of type TestService"):
            register_service(TestService, wrong_service)
    
    def test_multiple_services(self):
        test_service = TestService(50)
        another_service = AnotherService("test_name")
        
        register_service(TestService, test_service)
        register_service(AnotherService, another_service)
        
        retrieved_test = get_service(TestService)
        retrieved_another = get_service(AnotherService)
        
        assert retrieved_test is test_service
        assert retrieved_another is another_service
        assert retrieved_test.get_value() == 50
        assert retrieved_another.name == "test_name"
    
    def test_unregister_service(self):
        service = TestService(10)
        register_service(TestService, service)
        
        assert is_service_registered(TestService) is True
        
        locator = ServiceLocator()
        locator.unregister_service(TestService)
        
        assert is_service_registered(TestService) is False
    
    def test_clear_all_services(self):
        service1 = TestService(1)
        service2 = AnotherService("name")
        
        register_service(TestService, service1)
        register_service(AnotherService, service2)
        
        assert is_service_registered(TestService) is True
        assert is_service_registered(AnotherService) is True
        
        locator = ServiceLocator()
        locator.clear_all()
        
        assert is_service_registered(TestService) is False
        assert is_service_registered(AnotherService) is False
