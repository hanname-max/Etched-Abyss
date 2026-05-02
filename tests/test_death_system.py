"""
DeathSystem 测试

测试死亡系统的功能，包括事件订阅、实体销毁等。
"""

import pytest
from typing import Optional, List

from CoreLogic.ECS import BaseEntity
from CoreLogic import (
    HealthComponent,
    HealthSystem,
    DeathSystem,
    EntityDeathEvent,
    EntityManager,
    EventBus,
    ServiceLocator,
    register_service,
    subscribe,
    publish,
)


class TestDeathSystem:
    """DeathSystem 核心功能测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.death_system = DeathSystem()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_initial_state(self):
        """测试初始状态"""
        assert self.death_system.is_initialized() is False
    
    def test_initialize_sets_initialized(self):
        """测试 initialize 后状态变为已初始化"""
        self.death_system.initialize()
        assert self.death_system.is_initialized() is True
    
    def test_shutdown_clears_initialized(self):
        """测试 shutdown 后状态变为未初始化"""
        self.death_system.initialize()
        assert self.death_system.is_initialized() is True
        
        self.death_system.shutdown()
        assert self.death_system.is_initialized() is False
    
    def test_initialize_twice_is_safe(self):
        """测试多次 initialize 是安全的"""
        self.death_system.initialize()
        self.death_system.initialize()
        assert self.death_system.is_initialized() is True
    
    def test_shutdown_without_initialize_is_safe(self):
        """测试在未 initialize 时调用 shutdown 是安全的"""
        self.death_system.shutdown()
        assert self.death_system.is_initialized() is False
    
    def test_subscribes_to_entity_death_event_on_initialize(self):
        """测试 initialize 时订阅 EntityDeathEvent"""
        bus = EventBus()
        assert bus.get_subscriber_count(EntityDeathEvent) == 0
        
        self.death_system.initialize()
        
        assert bus.get_subscriber_count(EntityDeathEvent) == 1
    
    def test_unsubscribes_from_entity_death_event_on_shutdown(self):
        """测试 shutdown 时取消订阅 EntityDeathEvent"""
        bus = EventBus()
        self.death_system.initialize()
        assert bus.get_subscriber_count(EntityDeathEvent) == 1
        
        self.death_system.shutdown()
        
        assert bus.get_subscriber_count(EntityDeathEvent) == 0


class TestDeathSystemEntityDestruction:
    """DeathSystem 实体销毁功能测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.entity_manager = EntityManager()
        register_service(EntityManager, self.entity_manager)
        
        self.death_system = DeathSystem()
        self.death_system.initialize()
    
    def teardown_method(self):
        """每个测试后的清理"""
        self.death_system.shutdown()
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_entity_destruction_on_death_event(self):
        """测试收到死亡事件时销毁实体"""
        entity = self.entity_manager.create_entity()
        entity_id = entity.entity_id
        
        assert self.entity_manager.has_entity(entity_id) is True
        
        publish(EntityDeathEvent(entity_id=entity_id, max_health=100.0))
        
        assert self.entity_manager.has_entity(entity_id) is False
    
    def test_destroys_correct_entity(self):
        """测试销毁正确的实体"""
        entity1 = self.entity_manager.create_entity()
        entity2 = self.entity_manager.create_entity()
        entity3 = self.entity_manager.create_entity()
        
        assert self.entity_manager.get_entity_count() == 3
        
        publish(EntityDeathEvent(entity_id=entity2.entity_id, max_health=50.0))
        
        assert self.entity_manager.get_entity_count() == 2
        assert self.entity_manager.has_entity(entity1.entity_id) is True
        assert self.entity_manager.has_entity(entity2.entity_id) is False
        assert self.entity_manager.has_entity(entity3.entity_id) is True
    
    def test_nonexistent_entity_id_no_error(self):
        """测试对不存在的实体 ID 不报错"""
        publish(EntityDeathEvent(entity_id=99999, max_health=100.0))
        
        assert self.entity_manager.get_entity_count() == 0
    
    def test_shutdown_stops_destruction(self):
        """测试 shutdown 后不再销毁实体"""
        entity = self.entity_manager.create_entity()
        entity_id = entity.entity_id
        
        self.death_system.shutdown()
        
        publish(EntityDeathEvent(entity_id=entity_id, max_health=100.0))
        
        assert self.entity_manager.has_entity(entity_id) is True


class TestDeathSystemIntegration:
    """DeathSystem 集成测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.entity_manager = EntityManager()
        register_service(EntityManager, self.entity_manager)
        
        self.health_system = HealthSystem()
        self.death_system = DeathSystem()
        self.death_system.initialize()
    
    def teardown_method(self):
        """每个测试后的清理"""
        self.death_system.shutdown()
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_full_lifecycle_health_to_destruction(self):
        """测试完整生命周期：从受伤到死亡到销毁"""
        entity = self.entity_manager.create_entity()
        entity.add_component(HealthComponent(current_health=100.0, max_health=100.0))
        entity_id = entity.entity_id
        
        assert self.entity_manager.has_entity(entity_id) is True
        assert self.health_system.is_alive(entity) is True
        
        self.health_system.take_damage(entity, 100.0)
        
        assert self.health_system.is_alive(entity) is False
        assert self.entity_manager.has_entity(entity_id) is False
    
    def test_multiple_entities_death_and_destruction(self):
        """测试多个实体的死亡和销毁"""
        entity1 = self.entity_manager.create_entity()
        entity1.add_component(HealthComponent(current_health=50.0, max_health=50.0))
        
        entity2 = self.entity_manager.create_entity()
        entity2.add_component(HealthComponent(current_health=100.0, max_health=100.0))
        
        entity3 = self.entity_manager.create_entity()
        entity3.add_component(HealthComponent(current_health=75.0, max_health=75.0))
        
        assert self.entity_manager.get_entity_count() == 3
        
        self.health_system.take_damage(entity1, 50.0)
        assert self.entity_manager.get_entity_count() == 2
        
        self.health_system.take_damage(entity2, 200.0)
        assert self.entity_manager.get_entity_count() == 1
        
        assert self.entity_manager.has_entity(entity3.entity_id) is True
    
    def test_does_not_destroy_on_non_fatal_damage(self):
        """测试非致命伤害不会销毁实体"""
        entity = self.entity_manager.create_entity()
        entity.add_component(HealthComponent(current_health=100.0, max_health=100.0))
        entity_id = entity.entity_id
        
        self.health_system.take_damage(entity, 30.0)
        
        assert self.health_system.is_alive(entity) is True
        assert self.entity_manager.has_entity(entity_id) is True
        
        health = entity.get_component(HealthComponent)
        assert health.current_health == 70.0


class TestDeathSystemEdgeCases:
    """DeathSystem 边界情况测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.death_system = DeathSystem()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_no_entity_manager_no_error(self):
        """测试没有注册 EntityManager 时不报错"""
        self.death_system.initialize()
        
        publish(EntityDeathEvent(entity_id=1, max_health=100.0))
        
        assert True
    
    def test_zero_max_health_entity(self):
        """测试 max_health 为 0 的实体"""
        entity_manager = EntityManager()
        register_service(EntityManager, entity_manager)
        
        self.death_system.initialize()
        
        entity = entity_manager.create_entity()
        entity_id = entity.entity_id
        
        publish(EntityDeathEvent(entity_id=entity_id, max_health=0.0))
        
        assert entity_manager.has_entity(entity_id) is False
    
    def test_negative_max_health_entity(self):
        """测试 max_health 为负值的实体"""
        entity_manager = EntityManager()
        register_service(EntityManager, entity_manager)
        
        self.death_system.initialize()
        
        entity = entity_manager.create_entity()
        entity_id = entity.entity_id
        
        publish(EntityDeathEvent(entity_id=entity_id, max_health=-100.0))
        
        assert entity_manager.has_entity(entity_id) is False
