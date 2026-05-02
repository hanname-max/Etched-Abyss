"""
TargetingComponent 测试

测试 TargetingComponent 的索敌功能。
"""

import pytest

from CoreLogic import (
    TransformComponent,
    HealthComponent,
    TargetingComponent,
    EntityManager,
    ServiceLocator,
    register_service,
    EventBus,
)


class TestTargetingComponent:
    """TargetingComponent 测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_default_constructor(self):
        """测试默认构造函数"""
        targeting = TargetingComponent()
        assert targeting.search_radius == 1.0
        assert targeting.current_target_id is None
        assert targeting.transform is None
        assert targeting.entity_id is None
        assert targeting.has_target is False
    
    def test_parameterized_constructor(self):
        """测试带参数构造函数"""
        transform = TransformComponent(x=5.0, y=3.0)
        targeting = TargetingComponent(
            search_radius=3.0,
            transform=transform,
            entity_id=1,
        )
        assert targeting.search_radius == 3.0
        assert targeting.current_target_id is None
        assert targeting.transform is transform
        assert targeting.entity_id == 1
        assert targeting.has_target is False
    
    def test_clear_target(self):
        """测试清除目标"""
        targeting = TargetingComponent()
        targeting.current_target_id = 42
        assert targeting.has_target is True
        
        targeting.clear_target()
        assert targeting.current_target_id is None
        assert targeting.has_target is False
    
    def test_update_without_transform_does_nothing(self):
        """测试没有 transform 引用时 update 不做任何事"""
        targeting = TargetingComponent(
            search_radius=3.0,
            entity_id=1,
        )
        
        targeting.update(delta=1.0)
        
        assert targeting.current_target_id is None
        assert targeting.has_target is False
    
    def test_update_with_zero_radius_clears_target(self):
        """测试索敌半径为 0 时清除目标"""
        transform = TransformComponent(x=5.0, y=3.0)
        targeting = TargetingComponent(
            search_radius=0.0,
            transform=transform,
            entity_id=1,
        )
        targeting.current_target_id = 42
        
        targeting.update(delta=1.0)
        
        assert targeting.current_target_id is None
        assert targeting.has_target is False
    
    def test_update_with_negative_radius_clears_target(self):
        """测试索敌半径为负时清除目标"""
        transform = TransformComponent(x=5.0, y=3.0)
        targeting = TargetingComponent(
            search_radius=-1.0,
            transform=transform,
            entity_id=1,
        )
        targeting.current_target_id = 42
        
        targeting.update(delta=1.0)
        
        assert targeting.current_target_id is None


class TestTargetingComponentWithEntityManager:
    """TargetingComponent 与 EntityManager 集成测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        self.em = EntityManager()
        register_service(EntityManager, self.em)
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_no_enemies_in_range(self):
        """测试范围内没有敌人时 current_target_id 为 None"""
        tower = self.em.create_entity()
        tower_transform = TransformComponent(x=5.0, y=5.0)
        targeting = TargetingComponent(
            search_radius=2.0,
            transform=tower_transform,
            entity_id=tower.entity_id,
        )
        tower.add_component(tower_transform)
        tower.add_component(targeting)
        
        enemy = self.em.create_entity()
        enemy.add_component(TransformComponent(x=10.0, y=10.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        self.em.tick(delta=0.2)
        
        assert targeting.current_target_id is None
        assert targeting.has_target is False
    
    def test_single_enemy_in_range(self):
        """测试单个敌人在范围内时锁定该敌人"""
        tower = self.em.create_entity()
        tower_transform = TransformComponent(x=5.0, y=5.0)
        targeting = TargetingComponent(
            search_radius=3.0,
            transform=tower_transform,
            entity_id=tower.entity_id,
        )
        tower.add_component(tower_transform)
        tower.add_component(targeting)
        
        enemy = self.em.create_entity()
        enemy.add_component(TransformComponent(x=6.0, y=5.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        self.em.tick(delta=0.2)
        
        assert targeting.current_target_id == enemy.entity_id
        assert targeting.has_target is True
    
    def test_multiple_enemies_closest_first(self):
        """测试多个敌人时锁定距离最近的敌人"""
        tower = self.em.create_entity()
        tower_transform = TransformComponent(x=5.0, y=5.0)
        targeting = TargetingComponent(
            search_radius=5.0,
            transform=tower_transform,
            entity_id=tower.entity_id,
        )
        tower.add_component(tower_transform)
        tower.add_component(targeting)
        
        enemy_far = self.em.create_entity()
        enemy_far.add_component(TransformComponent(x=8.0, y=5.0))
        enemy_far.add_component(HealthComponent(current_health=100, max_health=100))
        
        enemy_close = self.em.create_entity()
        enemy_close.add_component(TransformComponent(x=6.0, y=5.0))
        enemy_close.add_component(HealthComponent(current_health=100, max_health=100))
        
        self.em.tick(delta=0.2)
        
        assert targeting.current_target_id == enemy_close.entity_id
        assert targeting.current_target_id != enemy_far.entity_id
    
    def test_tower_excludes_itself(self):
        """测试塔不会把自己当作目标（即使塔也有 HealthComponent）"""
        tower = self.em.create_entity()
        tower_transform = TransformComponent(x=5.0, y=5.0)
        targeting = TargetingComponent(
            search_radius=3.0,
            transform=tower_transform,
            entity_id=tower.entity_id,
        )
        tower.add_component(tower_transform)
        tower.add_component(targeting)
        tower.add_component(HealthComponent(current_health=200, max_health=200))
        
        self.em.tick(delta=0.2)
        
        assert targeting.current_target_id is None
        assert targeting.has_target is False
    
    def test_enemy_without_health_not_considered(self):
        """测试没有 HealthComponent 的实体不被视为敌人"""
        tower = self.em.create_entity()
        tower_transform = TransformComponent(x=5.0, y=5.0)
        targeting = TargetingComponent(
            search_radius=3.0,
            transform=tower_transform,
            entity_id=tower.entity_id,
        )
        tower.add_component(tower_transform)
        tower.add_component(targeting)
        
        not_enemy = self.em.create_entity()
        not_enemy.add_component(TransformComponent(x=6.0, y=5.0))
        
        self.em.tick(delta=0.2)
        
        assert targeting.current_target_id is None
    
    def test_enemy_without_transform_not_considered(self):
        """测试没有 TransformComponent 的实体不被视为敌人"""
        tower = self.em.create_entity()
        tower_transform = TransformComponent(x=5.0, y=5.0)
        targeting = TargetingComponent(
            search_radius=3.0,
            transform=tower_transform,
            entity_id=tower.entity_id,
        )
        tower.add_component(tower_transform)
        tower.add_component(targeting)
        
        not_enemy = self.em.create_entity()
        not_enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        self.em.tick(delta=0.2)
        
        assert targeting.current_target_id is None
    
    def test_enemy_moves_out_of_range(self):
        """测试敌人移出范围后目标被清除"""
        tower = self.em.create_entity()
        tower_transform = TransformComponent(x=5.0, y=5.0)
        targeting = TargetingComponent(
            search_radius=2.0,
            transform=tower_transform,
            entity_id=tower.entity_id,
        )
        tower.add_component(tower_transform)
        tower.add_component(targeting)
        
        enemy = self.em.create_entity()
        enemy_transform = TransformComponent(x=6.0, y=5.0)
        enemy.add_component(enemy_transform)
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        self.em.tick(delta=0.2)
        assert targeting.current_target_id == enemy.entity_id
        
        enemy_transform.x = 10.0
        self.em.tick(delta=0.2)
        
        assert targeting.current_target_id is None
    
    def test_closer_enemy_appears(self):
        """测试更近的敌人出现时切换目标"""
        tower = self.em.create_entity()
        tower_transform = TransformComponent(x=5.0, y=5.0)
        targeting = TargetingComponent(
            search_radius=5.0,
            transform=tower_transform,
            entity_id=tower.entity_id,
        )
        tower.add_component(tower_transform)
        tower.add_component(targeting)
        
        enemy_far = self.em.create_entity()
        enemy_far.add_component(TransformComponent(x=8.0, y=5.0))
        enemy_far.add_component(HealthComponent(current_health=100, max_health=100))
        
        self.em.tick(delta=0.2)
        assert targeting.current_target_id == enemy_far.entity_id
        
        enemy_close = self.em.create_entity()
        enemy_close.add_component(TransformComponent(x=6.0, y=5.0))
        enemy_close.add_component(HealthComponent(current_health=100, max_health=100))
        
        self.em.tick(delta=0.2)
        
        assert targeting.current_target_id == enemy_close.entity_id
    
    def test_scan_interval_controls_frequency(self):
        """测试扫描间隔控制扫描频率"""
        tower = self.em.create_entity()
        tower_transform = TransformComponent(x=5.0, y=5.0)
        targeting = TargetingComponent(
            search_radius=3.0,
            transform=tower_transform,
            entity_id=tower.entity_id,
            _scan_interval=1.0,
        )
        tower.add_component(tower_transform)
        tower.add_component(targeting)
        
        self.em.tick(delta=0.1)
        assert targeting.current_target_id is None
        
        enemy = self.em.create_entity()
        enemy.add_component(TransformComponent(x=6.0, y=5.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        self.em.tick(delta=0.1)
        assert targeting.current_target_id is None
        
        self.em.tick(delta=0.9)
        assert targeting.current_target_id == enemy.entity_id
    
    def test_diagonal_distance_calculation(self):
        """测试对角线距离计算"""
        tower = self.em.create_entity()
        tower_transform = TransformComponent(x=0.0, y=0.0)
        targeting = TargetingComponent(
            search_radius=5.0,
            transform=tower_transform,
            entity_id=tower.entity_id,
        )
        tower.add_component(tower_transform)
        tower.add_component(targeting)
        
        enemy_in_range = self.em.create_entity()
        enemy_in_range.add_component(TransformComponent(x=3.0, y=4.0))
        enemy_in_range.add_component(HealthComponent(current_health=100, max_health=100))
        
        enemy_out_of_range = self.em.create_entity()
        enemy_out_of_range.add_component(TransformComponent(x=4.0, y=4.0))
        enemy_out_of_range.add_component(HealthComponent(current_health=100, max_health=100))
        
        self.em.tick(delta=0.2)
        
        assert targeting.current_target_id == enemy_in_range.entity_id
