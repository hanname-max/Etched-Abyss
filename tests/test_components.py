"""
组件和系统测试

测试 TransformComponent、HealthComponent、HealthSystem 和 EntityDeathEvent 的功能。
"""

import pytest
from typing import Optional, List

from CoreLogic.ECS import BaseEntity
from CoreLogic import (
    TransformComponent,
    HealthComponent,
    HealthSystem,
    EntityDeathEvent,
    DeathContext,
    EventBus,
    ServiceLocator,
    GameLogger,
    IGameLogger,
    register_service,
    subscribe,
    unsubscribe,
)


class TestTransformComponent:
    """TransformComponent 测试"""
    
    def test_default_constructor(self):
        """测试默认构造函数"""
        transform = TransformComponent()
        assert transform.x == 0.0
        assert transform.y == 0.0
    
    def test_parameterized_constructor(self):
        """测试带参数构造函数"""
        transform = TransformComponent(x=5.5, y=3.2)
        assert transform.x == 5.5
        assert transform.y == 3.2
    
    def test_float_coordinates(self):
        """测试浮点坐标支持"""
        transform = TransformComponent(x=1.5, y=2.75)
        assert isinstance(transform.x, float)
        assert isinstance(transform.y, float)
        assert transform.x == 1.5
        assert transform.y == 2.75
    
    def test_mutable_coordinates(self):
        """测试坐标可变性"""
        transform = TransformComponent(x=1.0, y=1.0)
        transform.x += 2.5
        transform.y -= 0.5
        assert transform.x == 3.5
        assert transform.y == 0.5
    
    def test_add_to_entity(self):
        """测试添加到实体"""
        entity = BaseEntity(entity_id=1)
        transform = TransformComponent(x=10.0, y=20.0)
        entity.add_component(transform)
        
        retrieved = entity.get_component(TransformComponent)
        assert retrieved is transform
        assert retrieved.x == 10.0
        assert retrieved.y == 20.0


class TestHealthComponent:
    """HealthComponent 测试"""
    
    def test_constructor(self):
        """测试构造函数"""
        health = HealthComponent(current_health=100.0, max_health=100.0)
        assert health.current_health == 100.0
        assert health.max_health == 100.0
    
    def test_float_health(self):
        """测试浮点生命值支持"""
        health = HealthComponent(current_health=75.5, max_health=100.0)
        assert isinstance(health.current_health, float)
        assert isinstance(health.max_health, float)
        assert health.current_health == 75.5
    
    def test_mutable_health(self):
        """测试生命值可变性"""
        health = HealthComponent(current_health=100.0, max_health=100.0)
        health.current_health -= 25.0
        assert health.current_health == 75.0
    
    def test_add_to_entity(self):
        """测试添加到实体"""
        entity = BaseEntity(entity_id=1)
        health = HealthComponent(current_health=80.0, max_health=100.0)
        entity.add_component(health)
        
        retrieved = entity.get_component(HealthComponent)
        assert retrieved is health
        assert retrieved.current_health == 80.0
        assert retrieved.max_health == 100.0


class TestHealthSystem:
    """HealthSystem 测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.health_system = HealthSystem()
        self.entity = BaseEntity(entity_id=1)
        self.entity.add_component(HealthComponent(current_health=100.0, max_health=100.0))
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_take_damage_reduces_health(self):
        """测试扣血减少生命值"""
        remaining = self.health_system.take_damage(self.entity, 25.0)
        
        health = self.entity.get_component(HealthComponent)
        assert health.current_health == 75.0
        assert remaining == 75.0
    
    def test_take_damage_negative_amount_clamped(self):
        """测试负值伤害被钳制为 0"""
        remaining = self.health_system.take_damage(self.entity, -10.0)
        
        health = self.entity.get_component(HealthComponent)
        assert health.current_health == 100.0
        assert remaining == 100.0
    
    def test_take_damage_zero_amount(self):
        """测试 0 伤害"""
        remaining = self.health_system.take_damage(self.entity, 0.0)
        
        health = self.entity.get_component(HealthComponent)
        assert health.current_health == 100.0
        assert remaining == 100.0
    
    def test_take_damage_without_health_component(self):
        """测试对没有 HealthComponent 的实体扣血"""
        entity_without_health = BaseEntity(entity_id=2)
        remaining = self.health_system.take_damage(entity_without_health, 25.0)
        assert remaining == 0.0
    
    def test_heal_increases_health(self):
        """测试回血增加生命值"""
        health = self.entity.get_component(HealthComponent)
        health.current_health = 50.0
        
        remaining = self.health_system.heal(self.entity, 30.0)
        
        assert health.current_health == 80.0
        assert remaining == 80.0
    
    def test_heal_does_not_exceed_max(self):
        """测试回血不会超过最大生命值"""
        health = self.entity.get_component(HealthComponent)
        health.current_health = 90.0
        
        remaining = self.health_system.heal(self.entity, 20.0)
        
        assert health.current_health == 100.0
        assert remaining == 100.0
    
    def test_heal_negative_amount_clamped(self):
        """测试负值回血被钳制为 0"""
        health = self.entity.get_component(HealthComponent)
        health.current_health = 50.0
        
        remaining = self.health_system.heal(self.entity, -10.0)
        
        assert health.current_health == 50.0
        assert remaining == 50.0
    
    def test_is_alive_true(self):
        """测试 is_alive 返回 True"""
        assert self.health_system.is_alive(self.entity) is True
        
        self.health_system.take_damage(self.entity, 50.0)
        assert self.health_system.is_alive(self.entity) is True
    
    def test_is_alive_false(self):
        """测试 is_alive 返回 False"""
        self.health_system.take_damage(self.entity, 100.0)
        assert self.health_system.is_alive(self.entity) is False
        
        self.health_system.take_damage(self.entity, 50.0)
        assert self.health_system.is_alive(self.entity) is False
    
    def test_is_alive_without_component(self):
        """测试对没有 HealthComponent 的实体 is_alive"""
        entity_without_health = BaseEntity(entity_id=2)
        assert self.health_system.is_alive(entity_without_health) is False
    
    def test_get_health_percentage(self):
        """测试获取生命值百分比"""
        health = self.entity.get_component(HealthComponent)
        
        assert self.health_system.get_health_percentage(self.entity) == 1.0
        
        health.current_health = 50.0
        assert self.health_system.get_health_percentage(self.entity) == 0.5
        
        health.current_health = 0.0
        assert self.health_system.get_health_percentage(self.entity) == 0.0
        
        health.current_health = -10.0
        assert self.health_system.get_health_percentage(self.entity) == 0.0
    
    def test_get_health_percentage_without_component(self):
        """测试对没有 HealthComponent 的实体获取百分比"""
        entity_without_health = BaseEntity(entity_id=2)
        assert self.health_system.get_health_percentage(entity_without_health) == 0.0
    
    def test_take_damage_publishes_death_event(self):
        """测试扣血致死时发布死亡事件"""
        received_events: List[EntityDeathEvent] = []
        
        def on_death(event: EntityDeathEvent) -> None:
            received_events.append(event)
        
        subscribe(EntityDeathEvent, on_death)
        
        self.health_system.take_damage(self.entity, 100.0)
        
        assert len(received_events) == 1
        assert received_events[0].entity_id == 1
        assert received_events[0].max_health == 100.0
    
    def test_take_damage_does_not_publish_multiple_death_events(self):
        """测试死亡后继续扣血不会重复发布事件"""
        received_events: List[EntityDeathEvent] = []
        
        def on_death(event: EntityDeathEvent) -> None:
            received_events.append(event)
        
        subscribe(EntityDeathEvent, on_death)
        
        self.health_system.take_damage(self.entity, 100.0)
        self.health_system.take_damage(self.entity, 50.0)
        self.health_system.take_damage(self.entity, 50.0)
        
        assert len(received_events) == 1
    
    def test_register_on_death_callback(self):
        """测试注册死亡回调"""
        callback_called: List[DeathContext] = []
        
        def on_death(context: DeathContext) -> None:
            callback_called.append(context)
        
        self.health_system.register_on_death(self.entity.entity_id, on_death)
        self.health_system.take_damage(self.entity, 100.0)
        
        assert len(callback_called) == 1
        assert callback_called[0].entity_id == 1
        assert callback_called[0].max_health == 100.0
        assert callback_called[0].damage_dealt == 100.0
    
    def test_multiple_on_death_callbacks(self):
        """测试多个死亡回调"""
        callback1_called: List[DeathContext] = []
        callback2_called: List[DeathContext] = []
        
        def callback1(context: DeathContext) -> None:
            callback1_called.append(context)
        
        def callback2(context: DeathContext) -> None:
            callback2_called.append(context)
        
        self.health_system.register_on_death(self.entity.entity_id, callback1)
        self.health_system.register_on_death(self.entity.entity_id, callback2)
        self.health_system.take_damage(self.entity, 100.0)
        
        assert len(callback1_called) == 1
        assert len(callback2_called) == 1
    
    def test_unregister_on_death_callback(self):
        """测试注销死亡回调"""
        callback_called: List[DeathContext] = []
        
        def on_death(context: DeathContext) -> None:
            callback_called.append(context)
        
        self.health_system.register_on_death(self.entity.entity_id, on_death)
        self.health_system.unregister_on_death(self.entity.entity_id, on_death)
        self.health_system.take_damage(self.entity, 100.0)
        
        assert len(callback_called) == 0
    
    def test_clear_on_death(self):
        """测试清除所有死亡回调"""
        callback1_called: List[DeathContext] = []
        callback2_called: List[DeathContext] = []
        
        def callback1(context: DeathContext) -> None:
            callback1_called.append(context)
        
        def callback2(context: DeathContext) -> None:
            callback2_called.append(context)
        
        self.health_system.register_on_death(self.entity.entity_id, callback1)
        self.health_system.register_on_death(self.entity.entity_id, callback2)
        self.health_system.clear_on_death(self.entity.entity_id)
        self.health_system.take_damage(self.entity, 100.0)
        
        assert len(callback1_called) == 0
        assert len(callback2_called) == 0


class TestIntegration:
    """集成测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.logger = GameLogger()
        self.logger.set_min_level(0)
        register_service(IGameLogger, self.logger)
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_full_entity_lifecycle(self):
        """测试完整的实体生命周期"""
        entity = BaseEntity(entity_id=42)
        entity.add_component(TransformComponent(x=5.0, y=3.0))
        entity.add_component(HealthComponent(current_health=100.0, max_health=100.0))
        
        health_system = HealthSystem()
        
        death_events: List[EntityDeathEvent] = []
        subscribe(EntityDeathEvent, lambda e: death_events.append(e))
        
        assert health_system.is_alive(entity) is True
        assert health_system.get_health_percentage(entity) == 1.0
        
        health_system.take_damage(entity, 30.0)
        assert entity.get_component(HealthComponent).current_health == 70.0
        assert len(death_events) == 0
        
        health_system.heal(entity, 15.0)
        assert entity.get_component(HealthComponent).current_health == 85.0
        
        health_system.take_damage(entity, 90.0)
        assert entity.get_component(HealthComponent).current_health == -5.0
        assert health_system.is_alive(entity) is False
        assert len(death_events) == 1
        assert death_events[0].entity_id == 42
        
        transform = entity.get_component(TransformComponent)
        assert transform.x == 5.0
        assert transform.y == 3.0
