"""
攻击策略模式测试

测试策略模式的实现，包括：
- IAttackStrategy 接口
- SingleShotStrategy 单发策略
- MultiShotStrategy 多发策略（分裂神经效果）
- AttackComponent 策略切换
- AttackSystem 集成测试
"""

import pytest

from CoreLogic import (
    ServiceLocator,
    EventBus,
    register_service,
    EntityManager,
    TransformComponent,
    HealthComponent,
    TowerComponent,
    TargetingComponent,
    AttackComponent,
    ProjectileComponent,
    TowerFiredEvent,
    ProjectileSystem,
    AttackSystem,
    subscribe,
)
from CoreLogic.AttackStrategies import (
    SingleShotStrategy,
    MultiShotStrategy,
)
from CoreLogic.Interfaces import IAttackStrategy


class TestIAttackStrategy:
    """IAttackStrategy 接口测试"""
    
    def test_interface_is_abstract(self):
        """测试 IAttackStrategy 是抽象接口，不能直接实例化"""
        with pytest.raises(TypeError):
            IAttackStrategy()


class TestSingleShotStrategy:
    """SingleShotStrategy 单发策略测试"""
    
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
        strategy = SingleShotStrategy()
        
        assert strategy.strategy_id == "single_shot"
        assert strategy.projectile_speed > 0
    
    def test_parameterized_constructor(self):
        """测试带参数构造函数"""
        strategy = SingleShotStrategy(projectile_speed=10.0)
        
        assert strategy.projectile_speed == 10.0
    
    def test_execute_fire_publishes_event(self):
        """测试 execute_fire 发布 TowerFiredEvent"""
        fired_events = []
        
        def on_fired(event):
            fired_events.append(event)
        
        subscribe(TowerFiredEvent, on_fired)
        
        em = EntityManager()
        register_service(EntityManager, em)
        
        tower = em.create_entity()
        tower.add_component(TransformComponent(x=5.0, y=3.0))
        
        enemy = em.create_entity()
        enemy.add_component(TransformComponent(x=8.0, y=3.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        strategy = SingleShotStrategy(projectile_speed=8.0)
        
        projectile_count = strategy.execute_fire(
            tower_entity=tower,
            primary_target_id=enemy.entity_id,
            damage=25.0,
            status_effects=None
        )
        
        assert projectile_count == 1
        assert len(fired_events) == 1
        
        event = fired_events[0]
        assert event.tower_id == tower.entity_id
        assert event.target_id == enemy.entity_id
        assert event.damage == 25.0
        assert event.start_x == 5.0
        assert event.start_y == 3.0
        assert event.speed == 8.0


class TestMultiShotStrategy:
    """MultiShotStrategy 多发策略测试（分裂神经效果）"""
    
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
        strategy = MultiShotStrategy()
        
        assert strategy.strategy_id == "multi_shot"
        assert strategy.projectile_speed > 0
        assert strategy.split_radius > 0
        assert strategy.max_additional_targets >= 0
    
    def test_parameterized_constructor(self):
        """测试带参数构造函数"""
        strategy = MultiShotStrategy(
            projectile_speed=10.0,
            split_radius=3.0,
            max_additional_targets=3
        )
        
        assert strategy.projectile_speed == 10.0
        assert strategy.split_radius == 3.0
        assert strategy.max_additional_targets == 3
    
    def test_split_radius_setter(self):
        """测试 split_radius 属性设置"""
        strategy = MultiShotStrategy()
        strategy.split_radius = 4.0
        assert strategy.split_radius == 4.0
    
    def test_max_additional_targets_setter(self):
        """测试 max_additional_targets 属性设置"""
        strategy = MultiShotStrategy()
        strategy.max_additional_targets = 5
        assert strategy.max_additional_targets == 5
    
    def test_execute_fire_single_target(self):
        """测试只有主目标时 execute_fire 只发射一个投射物"""
        fired_events = []
        
        def on_fired(event):
            fired_events.append(event)
        
        subscribe(TowerFiredEvent, on_fired)
        
        em = EntityManager()
        register_service(EntityManager, em)
        
        tower = em.create_entity()
        tower.add_component(TransformComponent(x=5.0, y=3.0))
        
        enemy = em.create_entity()
        enemy.add_component(TransformComponent(x=8.0, y=3.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        strategy = MultiShotStrategy(
            projectile_speed=8.0,
            split_radius=2.0,
            max_additional_targets=2
        )
        
        projectile_count = strategy.execute_fire(
            tower_entity=tower,
            primary_target_id=enemy.entity_id,
            damage=25.0,
            status_effects=None
        )
        
        assert projectile_count == 1
        assert len(fired_events) == 1
    
    def test_execute_fire_multiple_targets(self):
        """测试主目标周围有敌人时发射多个投射物"""
        fired_events = []
        
        def on_fired(event):
            fired_events.append(event)
        
        subscribe(TowerFiredEvent, on_fired)
        
        em = EntityManager()
        register_service(EntityManager, em)
        
        tower = em.create_entity()
        tower.add_component(TransformComponent(x=5.0, y=3.0))
        
        primary_enemy = em.create_entity()
        primary_enemy.add_component(TransformComponent(x=8.0, y=3.0))
        primary_enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        enemy1 = em.create_entity()
        enemy1.add_component(TransformComponent(x=8.5, y=3.0))
        enemy1.add_component(HealthComponent(current_health=100, max_health=100))
        
        enemy2 = em.create_entity()
        enemy2.add_component(TransformComponent(x=7.5, y=3.5))
        enemy2.add_component(HealthComponent(current_health=100, max_health=100))
        
        strategy = MultiShotStrategy(
            projectile_speed=8.0,
            split_radius=2.0,
            max_additional_targets=2
        )
        
        projectile_count = strategy.execute_fire(
            tower_entity=tower,
            primary_target_id=primary_enemy.entity_id,
            damage=25.0,
            status_effects=None
        )
        
        assert projectile_count == 3
        assert len(fired_events) == 3
        
        target_ids = [event.target_id for event in fired_events]
        assert primary_enemy.entity_id in target_ids
        assert enemy1.entity_id in target_ids
        assert enemy2.entity_id in target_ids


class TestAttackComponent:
    """AttackComponent 攻击组件测试（策略模式上下文）"""
    
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
        attack = AttackComponent()
        
        assert attack.strategy_id == "single_shot"
        assert attack.is_ready is True
        assert attack.cooldown_remaining == 0.0
    
    def test_set_strategy(self):
        """测试设置新策略"""
        attack = AttackComponent()
        
        assert attack.strategy_id == "single_shot"
        
        multi = MultiShotStrategy()
        attack.set_strategy(multi)
        
        assert attack.strategy_id == "multi_shot"
    
    def test_reset_to_default(self):
        """测试重置到默认策略"""
        attack = AttackComponent()
        
        multi = MultiShotStrategy()
        attack.set_strategy(multi)
        assert attack.strategy_id == "multi_shot"
        
        attack.reset_to_default()
        assert attack.strategy_id == "single_shot"
    
    def test_cooldown_management(self):
        """测试冷却时间管理"""
        attack = AttackComponent()
        
        assert attack.is_ready is True
        assert attack.cooldown_remaining == 0.0
        
        attack.start_cooldown(1.0)
        assert attack.is_ready is False
        assert attack.cooldown_remaining == 1.0
        
        attack.update_cooldown(0.5)
        assert attack.cooldown_remaining == 0.5
        assert attack.is_ready is False
        
        attack.update_cooldown(0.6)
        assert attack.cooldown_remaining == 0.0
        assert attack.is_ready is True
    
    def test_execute_attack_delegates_to_strategy(self):
        """测试 execute_attack 委托给当前策略"""
        fired_events = []
        
        def on_fired(event):
            fired_events.append(event)
        
        subscribe(TowerFiredEvent, on_fired)
        
        em = EntityManager()
        register_service(EntityManager, em)
        
        tower = em.create_entity()
        tower.add_component(TransformComponent(x=5.0, y=3.0))
        
        enemy = em.create_entity()
        enemy.add_component(TransformComponent(x=8.0, y=3.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        attack = AttackComponent()
        
        projectile_count = attack.execute_attack(
            tower_entity=tower,
            target_id=enemy.entity_id,
            damage=25.0,
            status_effects=None
        )
        
        assert projectile_count == 1
        assert len(fired_events) == 1


class TestAttackSystem:
    """AttackSystem 攻击系统集成测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_initialize_and_shutdown(self):
        """测试初始化和关闭"""
        system = AttackSystem()
        
        assert system.is_initialized() is False
        
        system.initialize()
        assert system.is_initialized() is True
        
        system.shutdown()
        assert system.is_initialized() is False
    
    def test_double_initialize_does_nothing(self):
        """测试重复初始化不产生副作用"""
        system = AttackSystem()
        
        system.initialize()
        assert system.is_initialized() is True
        
        system.initialize()
        assert system.is_initialized() is True
    
    def test_tick_updates_cooldown(self):
        """测试 tick 更新冷却时间"""
        em = EntityManager()
        register_service(EntityManager, em)
        
        tower = em.create_entity()
        tower.add_component(TowerComponent(
            config_id="tower_test",
            name="Test Tower",
            cost=100,
            damage=20,
            attack_range=3.0,
            attack_speed=1.0
        ))
        tower.add_component(TransformComponent(x=5.0, y=3.0))
        tower.add_component(TargetingComponent(
            search_radius=3.0,
            entity_id=tower.entity_id
        ))
        attack = AttackComponent()
        tower.add_component(attack)
        
        attack.start_cooldown(1.0)
        assert attack.is_ready is False
        
        system = AttackSystem()
        system.initialize()
        
        system.tick(delta=0.5)
        assert attack.cooldown_remaining == 0.5
        
        system.tick(delta=0.6)
        assert attack.cooldown_remaining == 0.0
        assert attack.is_ready is True
    
    def test_tick_triggers_attack_when_ready(self):
        """测试冷却完成且有目标时自动触发攻击"""
        fired_events = []
        
        def on_fired(event):
            fired_events.append(event)
        
        subscribe(TowerFiredEvent, on_fired)
        
        em = EntityManager()
        register_service(EntityManager, em)
        
        projectile_system = ProjectileSystem()
        projectile_system.initialize()
        
        tower = em.create_entity()
        tower.add_component(TowerComponent(
            config_id="tower_test",
            name="Test Tower",
            cost=100,
            damage=25,
            attack_range=3.0,
            attack_speed=1.0
        ))
        tower_transform = TransformComponent(x=5.0, y=3.0)
        tower.add_component(tower_transform)
        
        targeting = TargetingComponent(
            search_radius=3.0,
            transform=tower_transform,
            entity_id=tower.entity_id
        )
        tower.add_component(targeting)
        
        attack = AttackComponent()
        tower.add_component(attack)
        
        enemy = em.create_entity()
        enemy.add_component(TransformComponent(x=7.0, y=3.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        em.tick(delta=0.2)
        
        assert targeting.current_target_id == enemy.entity_id
        
        system = AttackSystem()
        system.initialize()
        
        assert attack.is_ready is True
        assert len(fired_events) == 0
        
        system.tick(delta=0.1)
        
        assert len(fired_events) == 1
        assert attack.is_ready is False
        assert attack.cooldown_remaining > 0
        
        event = fired_events[0]
        assert event.tower_id == tower.entity_id
        assert event.target_id == enemy.entity_id
        assert event.damage == 25.0


class TestStrategyPatternEndToEnd:
    """策略模式端到端测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_switching_strategy_changes_attack_behavior(self):
        """测试切换策略改变攻击行为（分裂神经器官效果）"""
        fired_events = []
        
        def on_fired(event):
            fired_events.append(event)
        
        subscribe(TowerFiredEvent, on_fired)
        
        em = EntityManager()
        register_service(EntityManager, em)
        
        tower = em.create_entity()
        tower.add_component(TowerComponent(
            config_id="tower_test",
            name="Test Tower",
            cost=100,
            damage=25,
            attack_range=5.0,
            attack_speed=1.0
        ))
        tower_transform = TransformComponent(x=5.0, y=3.0)
        tower.add_component(tower_transform)
        
        targeting = TargetingComponent(
            search_radius=5.0,
            transform=tower_transform,
            entity_id=tower.entity_id
        )
        tower.add_component(targeting)
        
        attack = AttackComponent()
        tower.add_component(attack)
        
        primary_enemy = em.create_entity()
        primary_enemy.add_component(TransformComponent(x=5.5, y=3.0))
        primary_enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        enemy1 = em.create_entity()
        enemy1.add_component(TransformComponent(x=6.0, y=3.0))
        enemy1.add_component(HealthComponent(current_health=100, max_health=100))
        
        enemy2 = em.create_entity()
        enemy2.add_component(TransformComponent(x=5.5, y=3.5))
        enemy2.add_component(HealthComponent(current_health=100, max_health=100))
        
        em.tick(delta=0.2)
        
        assert targeting.current_target_id is not None
        assert attack.strategy_id == "single_shot"
        
        system = AttackSystem()
        system.initialize()
        
        system.tick(delta=0.1)
        
        assert len(fired_events) == 1
        assert attack.is_ready is False
        
        attack.cooldown_remaining = 0.0
        
        multi_shot = MultiShotStrategy(
            split_radius=2.0,
            max_additional_targets=2
        )
        attack.set_strategy(multi_shot)
        
        assert attack.strategy_id == "multi_shot"
        assert attack.is_ready is True
        
        system.tick(delta=0.1)
        
        assert len(fired_events) == 4
        assert attack.is_ready is False
        
        attack.cooldown_remaining = 0.0
        attack.reset_to_default()
        
        assert attack.strategy_id == "single_shot"
