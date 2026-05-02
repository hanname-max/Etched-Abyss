"""
投射物系统测试

测试 ProjectileSystem、HomingMovementComponent 和相关事件的功能。
"""

import pytest

from CoreLogic import (
    TransformComponent,
    HealthComponent,
    ProjectileComponent,
    HomingMovementComponent,
    EntityManager,
    ServiceLocator,
    register_service,
    EventBus,
    TowerFiredEvent,
    ProjectileHitEvent,
    ProjectileSystem,
    publish,
    subscribe,
)


class TestTowerFiredEvent:
    """TowerFiredEvent 测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_event_creation(self):
        """测试事件创建"""
        event = TowerFiredEvent(
            tower_id=1,
            target_id=5,
            damage=25.0,
            start_x=5.0,
            start_y=3.0,
            speed=8.0
        )
        
        assert event.tower_id == 1
        assert event.target_id == 5
        assert event.damage == 25.0
        assert event.start_x == 5.0
        assert event.start_y == 3.0
        assert event.speed == 8.0


class TestProjectileHitEvent:
    """ProjectileHitEvent 测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_event_creation(self):
        """测试事件创建"""
        event = ProjectileHitEvent(
            projectile_id=10,
            target_id=5,
            damage=25.0,
            hit_x=6.0,
            hit_y=3.0
        )
        
        assert event.projectile_id == 10
        assert event.target_id == 5
        assert event.damage == 25.0
        assert event.hit_x == 6.0
        assert event.hit_y == 3.0


class TestProjectileComponent:
    """ProjectileComponent 测试"""
    
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
        projectile = ProjectileComponent(
            damage=25.0,
            target_id=5
        )
        
        assert projectile.damage == 25.0
        assert projectile.target_id == 5
        assert projectile.source_tower_id is None
        assert projectile.is_active is True
        assert projectile.hit_threshold == 0.1
    
    def test_parameterized_constructor(self):
        """测试带参数构造函数"""
        projectile = ProjectileComponent(
            damage=50.0,
            target_id=10,
            source_tower_id=1,
            hit_threshold=0.2
        )
        
        assert projectile.damage == 50.0
        assert projectile.target_id == 10
        assert projectile.source_tower_id == 1
        assert projectile.is_active is True
        assert projectile.hit_threshold == 0.2
    
    def test_set_inactive(self):
        """测试设置为非活动状态"""
        projectile = ProjectileComponent(
            damage=25.0,
            target_id=5
        )
        
        assert projectile.is_active is True
        projectile.is_active = False
        assert projectile.is_active is False


class TestHomingMovementComponent:
    """HomingMovementComponent 测试"""
    
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
        transform = TransformComponent(x=5.0, y=3.0)
        projectile_comp = ProjectileComponent(
            damage=25.0,
            target_id=5,
            hit_threshold=0.1
        )
        
        homing = HomingMovementComponent(
            speed=8.0,
            target_id=5,
            projectile_id=10,
            transform=transform,
            projectile_component=projectile_comp
        )
        
        assert homing.speed == 8.0
        assert homing.target_id == 5
        assert homing.projectile_id == 10
        assert homing.transform is transform
        assert homing.projectile_component is projectile_comp
        assert homing.is_active is True
    
    def test_is_active_property(self):
        """测试 is_active 属性"""
        transform = TransformComponent(x=5.0, y=3.0)
        projectile_comp = ProjectileComponent(
            damage=25.0,
            target_id=5
        )
        
        homing = HomingMovementComponent(
            speed=8.0,
            target_id=5,
            projectile_id=10,
            transform=transform,
            projectile_component=projectile_comp
        )
        
        assert homing.is_active is True
        
        homing._has_hit = True
        assert homing.is_active is False
        
        homing._has_hit = False
        homing._target_lost = True
        assert homing.is_active is False


class TestHomingMovementComponentWithEntityManager:
    """HomingMovementComponent 与 EntityManager 集成测试"""
    
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
    
    def test_projectile_moves_towards_target(self):
        """测试投射物向目标移动"""
        enemy = self.em.create_entity()
        enemy.add_component(TransformComponent(x=10.0, y=5.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        projectile = self.em.create_entity()
        transform = TransformComponent(x=5.0, y=5.0)
        projectile_comp = ProjectileComponent(
            damage=25.0,
            target_id=enemy.entity_id,
            hit_threshold=0.1
        )
        homing = HomingMovementComponent(
            speed=5.0,
            target_id=enemy.entity_id,
            projectile_id=projectile.entity_id,
            transform=transform,
            projectile_component=projectile_comp
        )
        projectile.add_component(transform)
        projectile.add_component(projectile_comp)
        projectile.add_component(homing)
        
        initial_x = transform.x
        self.em.tick(delta=0.5)
        
        assert transform.x > initial_x
        assert transform.y == 5.0
    
    def test_projectile_hits_target(self):
        """测试投射物击中目标"""
        hit_events = []
        
        def on_hit(event: ProjectileHitEvent):
            hit_events.append(event)
        
        subscribe(ProjectileHitEvent, on_hit)
        
        enemy = self.em.create_entity()
        enemy_transform = TransformComponent(x=5.5, y=5.0)
        enemy.add_component(enemy_transform)
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        projectile = self.em.create_entity()
        transform = TransformComponent(x=5.0, y=5.0)
        projectile_comp = ProjectileComponent(
            damage=25.0,
            target_id=enemy.entity_id,
            hit_threshold=0.6
        )
        homing = HomingMovementComponent(
            speed=10.0,
            target_id=enemy.entity_id,
            projectile_id=projectile.entity_id,
            transform=transform,
            projectile_component=projectile_comp
        )
        projectile.add_component(transform)
        projectile.add_component(projectile_comp)
        projectile.add_component(homing)
        
        self.em.tick(delta=0.2)
        
        assert len(hit_events) == 1
        assert hit_events[0].projectile_id == projectile.entity_id
        assert hit_events[0].target_id == enemy.entity_id
        assert hit_events[0].damage == 25.0
        assert homing.is_active is False
        assert projectile_comp.is_active is False
    
    def test_target_lost_when_entity_destroyed(self):
        """测试目标实体被销毁时目标丢失"""
        enemy = self.em.create_entity()
        enemy.add_component(TransformComponent(x=10.0, y=5.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        projectile = self.em.create_entity()
        transform = TransformComponent(x=5.0, y=5.0)
        projectile_comp = ProjectileComponent(
            damage=25.0,
            target_id=enemy.entity_id,
            hit_threshold=0.1
        )
        homing = HomingMovementComponent(
            speed=5.0,
            target_id=enemy.entity_id,
            projectile_id=projectile.entity_id,
            transform=transform,
            projectile_component=projectile_comp
        )
        projectile.add_component(transform)
        projectile.add_component(projectile_comp)
        projectile.add_component(homing)
        
        self.em.destroy_entity(enemy.entity_id)
        self.em.tick(delta=0.1)
        
        assert homing._target_lost is True
        assert homing.is_active is False
    
    def test_target_lost_when_health_zero(self):
        """测试目标生命值为 0 时目标丢失"""
        enemy = self.em.create_entity()
        enemy.add_component(TransformComponent(x=10.0, y=5.0))
        enemy_health = HealthComponent(current_health=0, max_health=100)
        enemy.add_component(enemy_health)
        
        projectile = self.em.create_entity()
        transform = TransformComponent(x=5.0, y=5.0)
        projectile_comp = ProjectileComponent(
            damage=25.0,
            target_id=enemy.entity_id,
            hit_threshold=0.1
        )
        homing = HomingMovementComponent(
            speed=5.0,
            target_id=enemy.entity_id,
            projectile_id=projectile.entity_id,
            transform=transform,
            projectile_component=projectile_comp
        )
        projectile.add_component(transform)
        projectile.add_component(projectile_comp)
        projectile.add_component(homing)
        
        self.em.tick(delta=0.1)
        
        assert homing._target_lost is True
        assert homing.is_active is False


class TestProjectileSystem:
    """ProjectileSystem 测试"""
    
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
    
    def test_initialize_and_shutdown(self):
        """测试初始化和关闭"""
        system = ProjectileSystem()
        
        assert system.is_initialized() is False
        
        system.initialize()
        assert system.is_initialized() is True
        
        system.shutdown()
        assert system.is_initialized() is False
    
    def test_double_initialize_does_nothing(self):
        """测试重复初始化不产生副作用"""
        system = ProjectileSystem()
        
        system.initialize()
        assert system.is_initialized() is True
        
        system.initialize()
        assert system.is_initialized() is True
    
    def test_create_projectile_on_tower_fired(self):
        """测试 TowerFiredEvent 触发时创建投射物"""
        system = ProjectileSystem()
        system.initialize()
        
        initial_entity_count = self.em.get_entity_count()
        
        enemy = self.em.create_entity()
        enemy.add_component(TransformComponent(x=10.0, y=5.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        event = TowerFiredEvent(
            tower_id=1,
            target_id=enemy.entity_id,
            damage=25.0,
            start_x=5.0,
            start_y=3.0,
            speed=8.0
        )
        publish(event)
        
        assert self.em.get_entity_count() == initial_entity_count + 2
        
        projectiles = self.em.get_entities_with_component(ProjectileComponent)
        assert len(projectiles) == 1
        
        projectile = projectiles[0]
        projectile_comp = projectile.get_component(ProjectileComponent)
        transform = projectile.get_component(TransformComponent)
        homing = projectile.get_component(HomingMovementComponent)
        
        assert projectile_comp is not None
        assert transform is not None
        assert homing is not None
        assert projectile_comp.damage == 25.0
        assert projectile_comp.target_id == enemy.entity_id
        assert projectile_comp.source_tower_id == 1
        assert transform.x == 5.0
        assert transform.y == 3.0
        assert homing.speed == 8.0
    
    def test_destroy_projectile_on_hit(self):
        """测试 ProjectileHitEvent 触发时销毁投射物"""
        system = ProjectileSystem()
        system.initialize()
        
        enemy = self.em.create_entity()
        enemy.add_component(TransformComponent(x=10.0, y=5.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        fire_event = TowerFiredEvent(
            tower_id=1,
            target_id=enemy.entity_id,
            damage=25.0,
            start_x=5.0,
            start_y=3.0,
            speed=8.0
        )
        publish(fire_event)
        
        projectiles = self.em.get_entities_with_component(ProjectileComponent)
        assert len(projectiles) == 1
        projectile_id = projectiles[0].entity_id
        
        hit_event = ProjectileHitEvent(
            projectile_id=projectile_id,
            target_id=enemy.entity_id,
            damage=25.0,
            hit_x=10.0,
            hit_y=5.0
        )
        publish(hit_event)
        
        assert self.em.get_entity(projectile_id) is None
    
    def test_get_active_projectile_count(self):
        """测试获取活动投射物数量"""
        system = ProjectileSystem()
        system.initialize()
        
        assert system.get_active_projectile_count() == 0
        
        enemy = self.em.create_entity()
        enemy.add_component(TransformComponent(x=10.0, y=5.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        fire_event = TowerFiredEvent(
            tower_id=1,
            target_id=enemy.entity_id,
            damage=25.0,
            start_x=5.0,
            start_y=3.0,
            speed=8.0
        )
        publish(fire_event)
        publish(fire_event)
        
        assert system.get_active_projectile_count() == 2
    
    def test_tick_cleans_up_inactive_projectiles(self):
        """测试 tick 方法清理非活动投射物"""
        system = ProjectileSystem()
        system.initialize()
        
        enemy = self.em.create_entity()
        enemy.add_component(TransformComponent(x=10.0, y=5.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        fire_event = TowerFiredEvent(
            tower_id=1,
            target_id=enemy.entity_id,
            damage=25.0,
            start_x=5.0,
            start_y=3.0,
            speed=8.0
        )
        publish(fire_event)
        
        assert system.get_active_projectile_count() == 1
        
        projectiles = self.em.get_entities_with_component(ProjectileComponent)
        projectile_comp = projectiles[0].get_component(ProjectileComponent)
        projectile_comp.is_active = False
        
        system.tick(delta=0.1)
        
        assert system.get_active_projectile_count() == 0


class TestEndToEndProjectileFlow:
    """端到端投射物流程测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        self.em = EntityManager()
        register_service(EntityManager, self.em)
        
        self.projectile_system = ProjectileSystem()
        self.projectile_system.initialize()
        
        self.hit_events = []
        
        def on_hit(event: ProjectileHitEvent):
            self.hit_events.append(event)
        
        subscribe(ProjectileHitEvent, on_hit)
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_complete_projectile_lifecycle(self):
        """测试完整的投射物生命周期"""
        enemy = self.em.create_entity()
        enemy_transform = TransformComponent(x=6.0, y=5.0)
        enemy.add_component(enemy_transform)
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        publish(TowerFiredEvent(
            tower_id=1,
            target_id=enemy.entity_id,
            damage=30.0,
            start_x=5.0,
            start_y=5.0,
            speed=5.0
        ))
        
        assert self.projectile_system.get_active_projectile_count() == 1
        
        self.em.tick(delta=0.3)
        
        assert len(self.hit_events) == 1
        assert self.hit_events[0].damage == 30.0
        assert self.hit_events[0].target_id == enemy.entity_id
        
        self.projectile_system.tick(delta=0.1)
        assert self.projectile_system.get_active_projectile_count() == 0
