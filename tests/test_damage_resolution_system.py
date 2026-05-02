"""
DamageResolutionSystem 测试

测试伤害结算系统的功能，包括事件订阅、目标存活验证、伤害结算等。
"""

import pytest
from typing import List

from CoreLogic import (
    HealthComponent,
    HealthSystem,
    DeathSystem,
    DamageResolutionSystem,
    ProjectileHitEvent,
    EntityDeathEvent,
    EntityManager,
    EventBus,
    ServiceLocator,
    register_service,
    publish,
)


class TestDamageResolutionSystem:
    """DamageResolutionSystem 核心功能测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.damage_resolution_system = DamageResolutionSystem()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_initial_state(self):
        """测试初始状态"""
        assert self.damage_resolution_system.is_initialized() is False
    
    def test_initialize_sets_initialized(self):
        """测试 initialize 后状态变为已初始化"""
        self.damage_resolution_system.initialize()
        assert self.damage_resolution_system.is_initialized() is True
    
    def test_shutdown_clears_initialized(self):
        """测试 shutdown 后状态变为未初始化"""
        self.damage_resolution_system.initialize()
        assert self.damage_resolution_system.is_initialized() is True
        
        self.damage_resolution_system.shutdown()
        assert self.damage_resolution_system.is_initialized() is False
    
    def test_initialize_twice_is_safe(self):
        """测试多次 initialize 是安全的"""
        self.damage_resolution_system.initialize()
        self.damage_resolution_system.initialize()
        assert self.damage_resolution_system.is_initialized() is True
    
    def test_shutdown_without_initialize_is_safe(self):
        """测试在未 initialize 时调用 shutdown 是安全的"""
        self.damage_resolution_system.shutdown()
        assert self.damage_resolution_system.is_initialized() is False
    
    def test_subscribes_to_projectile_hit_event_on_initialize(self):
        """测试 initialize 时订阅 ProjectileHitEvent"""
        bus = EventBus()
        assert bus.get_subscriber_count(ProjectileHitEvent) == 0
        
        self.damage_resolution_system.initialize()
        
        assert bus.get_subscriber_count(ProjectileHitEvent) == 1
    
    def test_unsubscribes_from_projectile_hit_event_on_shutdown(self):
        """测试 shutdown 时取消订阅 ProjectileHitEvent"""
        bus = EventBus()
        self.damage_resolution_system.initialize()
        assert bus.get_subscriber_count(ProjectileHitEvent) == 1
        
        self.damage_resolution_system.shutdown()
        
        assert bus.get_subscriber_count(ProjectileHitEvent) == 0


class TestDamageResolutionSystemTargetValidation:
    """DamageResolutionSystem 目标存活验证测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.entity_manager = EntityManager()
        register_service(EntityManager, self.entity_manager)
        
        self.damage_resolution_system = DamageResolutionSystem()
        self.damage_resolution_system.initialize()
    
    def teardown_method(self):
        """每个测试后的清理"""
        self.damage_resolution_system.shutdown()
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_no_damage_when_target_does_not_exist(self):
        """测试目标不存在时不造成伤害"""
        publish(ProjectileHitEvent(
            projectile_id=10,
            target_id=999,
            damage=25.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        assert self.entity_manager.get_entity_count() == 0
    
    def test_no_damage_when_target_has_no_health_component(self):
        """测试目标没有 HealthComponent 时不造成伤害"""
        enemy = self.entity_manager.create_entity()
        
        publish(ProjectileHitEvent(
            projectile_id=10,
            target_id=enemy.entity_id,
            damage=25.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        assert self.entity_manager.has_entity(enemy.entity_id) is True
    
    def test_no_damage_when_target_already_dead(self):
        """测试目标已死亡时不造成伤害"""
        enemy = self.entity_manager.create_entity()
        enemy.add_component(HealthComponent(current_health=0.0, max_health=100.0))
        
        publish(ProjectileHitEvent(
            projectile_id=10,
            target_id=enemy.entity_id,
            damage=25.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        health = enemy.get_component(HealthComponent)
        assert health.current_health == 0.0


class TestDamageResolutionSystemDamageApplication:
    """DamageResolutionSystem 伤害结算测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.entity_manager = EntityManager()
        register_service(EntityManager, self.entity_manager)
        
        self.damage_resolution_system = DamageResolutionSystem()
        self.damage_resolution_system.initialize()
    
    def teardown_method(self):
        """每个测试后的清理"""
        self.damage_resolution_system.shutdown()
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_applies_damage_to_alive_target(self):
        """测试对存活目标造成伤害"""
        enemy = self.entity_manager.create_entity()
        enemy.add_component(HealthComponent(current_health=100.0, max_health=100.0))
        
        publish(ProjectileHitEvent(
            projectile_id=10,
            target_id=enemy.entity_id,
            damage=25.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        health = enemy.get_component(HealthComponent)
        assert health.current_health == 75.0
    
    def test_applies_multiple_hits(self):
        """测试多次击中造成多次伤害"""
        enemy = self.entity_manager.create_entity()
        enemy.add_component(HealthComponent(current_health=100.0, max_health=100.0))
        
        publish(ProjectileHitEvent(
            projectile_id=10,
            target_id=enemy.entity_id,
            damage=20.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        publish(ProjectileHitEvent(
            projectile_id=11,
            target_id=enemy.entity_id,
            damage=30.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        health = enemy.get_component(HealthComponent)
        assert health.current_health == 50.0
    
    def test_format_hit_message_with_tower_id(self):
        """测试格式化包含防御塔 ID 的消息"""
        message = self.damage_resolution_system._format_hit_message(ProjectileHitEvent(
            projectile_id=10,
            target_id=5,
            damage=25.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        assert "防御塔 1 的投射物命中了敌人 5" in message
        assert "造成了 25.0 点伤害" in message
    
    def test_format_hit_message_without_tower_id(self):
        """测试格式化不包含防御塔 ID 的消息"""
        message = self.damage_resolution_system._format_hit_message(ProjectileHitEvent(
            projectile_id=10,
            target_id=5,
            damage=25.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=None
        ))
        
        assert "防御塔 未知 的投射物命中了敌人 5" in message
        assert "造成了 25.0 点伤害" in message


class TestDamageResolutionSystemIntegration:
    """DamageResolutionSystem 完整集成测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.entity_manager = EntityManager()
        register_service(EntityManager, self.entity_manager)
        
        self.death_system = DeathSystem()
        self.death_system.initialize()
        
        self.damage_resolution_system = DamageResolutionSystem()
        self.damage_resolution_system.initialize()
        
        self.death_events: List[EntityDeathEvent] = []
        
        def on_death(event: EntityDeathEvent):
            self.death_events.append(event)
        
        from CoreLogic import subscribe
        subscribe(EntityDeathEvent, on_death)
    
    def teardown_method(self):
        """每个测试后的清理"""
        self.damage_resolution_system.shutdown()
        self.death_system.shutdown()
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_non_fatal_damage_does_not_kill(self):
        """测试非致命伤害不会击杀"""
        enemy = self.entity_manager.create_entity()
        enemy.add_component(HealthComponent(current_health=100.0, max_health=100.0))
        enemy_id = enemy.entity_id
        
        publish(ProjectileHitEvent(
            projectile_id=10,
            target_id=enemy_id,
            damage=30.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        assert self.entity_manager.has_entity(enemy_id) is True
        assert len(self.death_events) == 0
        
        health = enemy.get_component(HealthComponent)
        assert health.current_health == 70.0
    
    def test_fatal_damage_triggers_death_and_destruction(self):
        """测试致命伤害触发死亡和销毁"""
        enemy = self.entity_manager.create_entity()
        enemy.add_component(HealthComponent(current_health=50.0, max_health=100.0))
        enemy_id = enemy.entity_id
        
        publish(ProjectileHitEvent(
            projectile_id=10,
            target_id=enemy_id,
            damage=60.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        assert len(self.death_events) == 1
        assert self.death_events[0].entity_id == enemy_id
        assert self.death_events[0].max_health == 100.0
        
        assert self.entity_manager.has_entity(enemy_id) is False
    
    def test_multiple_enemies_damage_independently(self):
        """测试多个敌人独立受到伤害"""
        enemy1 = self.entity_manager.create_entity()
        enemy1.add_component(HealthComponent(current_health=100.0, max_health=100.0))
        enemy1_id = enemy1.entity_id
        
        enemy2 = self.entity_manager.create_entity()
        enemy2.add_component(HealthComponent(current_health=80.0, max_health=80.0))
        enemy2_id = enemy2.entity_id
        
        publish(ProjectileHitEvent(
            projectile_id=10,
            target_id=enemy1_id,
            damage=50.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        publish(ProjectileHitEvent(
            projectile_id=11,
            target_id=enemy2_id,
            damage=90.0,
            hit_x=6.0,
            hit_y=5.0,
            source_tower_id=2
        ))
        
        assert self.entity_manager.has_entity(enemy1_id) is True
        health1 = enemy1.get_component(HealthComponent)
        assert health1.current_health == 50.0
        
        assert self.entity_manager.has_entity(enemy2_id) is False
        assert len(self.death_events) == 1
        assert self.death_events[0].entity_id == enemy2_id


class TestDamageResolutionSystemEdgeCases:
    """DamageResolutionSystem 边界情况测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.damage_resolution_system = DamageResolutionSystem()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_no_entity_manager_no_error(self):
        """测试没有注册 EntityManager 时不报错"""
        self.damage_resolution_system.initialize()
        
        publish(ProjectileHitEvent(
            projectile_id=10,
            target_id=5,
            damage=25.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        assert True
    
    def test_zero_damage(self):
        """测试 0 点伤害"""
        entity_manager = EntityManager()
        register_service(EntityManager, entity_manager)
        
        self.damage_resolution_system.initialize()
        
        enemy = entity_manager.create_entity()
        enemy.add_component(HealthComponent(current_health=100.0, max_health=100.0))
        
        publish(ProjectileHitEvent(
            projectile_id=10,
            target_id=enemy.entity_id,
            damage=0.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        health = enemy.get_component(HealthComponent)
        assert health.current_health == 100.0
    
    def test_negative_damage_treated_as_zero(self):
        """测试负伤害被视为 0"""
        entity_manager = EntityManager()
        register_service(EntityManager, entity_manager)
        
        self.damage_resolution_system.initialize()
        
        enemy = entity_manager.create_entity()
        enemy.add_component(HealthComponent(current_health=100.0, max_health=100.0))
        
        publish(ProjectileHitEvent(
            projectile_id=10,
            target_id=enemy.entity_id,
            damage=-50.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        health = enemy.get_component(HealthComponent)
        assert health.current_health == 100.0
    
    def test_target_destroyed_while_projectile_flying(self):
        """测试投射物飞行期间目标被其他塔摧毁"""
        entity_manager = EntityManager()
        register_service(EntityManager, entity_manager)
        
        self.damage_resolution_system.initialize()
        
        enemy = entity_manager.create_entity()
        enemy.add_component(HealthComponent(current_health=50.0, max_health=100.0))
        enemy_id = enemy.entity_id
        
        entity_manager.destroy_entity(enemy_id)
        
        publish(ProjectileHitEvent(
            projectile_id=10,
            target_id=enemy_id,
            damage=30.0,
            hit_x=5.0,
            hit_y=5.0,
            source_tower_id=1
        ))
        
        assert entity_manager.has_entity(enemy_id) is False
