"""
攻城模式单元测试

测试攻城模式 AI 机制，包括：
1. SiegeComponent 攻城状态组件
2. DynamicRepathingSystem 重寻路失败时触发攻城状态
3. SiegeSystem 攻城状态系统：敌人攻击塔
4. DeathSystem 防御塔死亡时恢复网格可通行性
5. 塔被摧毁后敌人重寻路
"""

import pytest
from typing import Optional, List
from collections import deque

from CoreLogic import (
    ServiceLocator,
    register_service,
    get_service,
    EventBus,
    subscribe,
    unsubscribe,
    publish,
    IDataLoader,
    IGameLogger,
    EntityManager,
    GridMap,
    Pathfinder,
    MockDataLoader,
    GameLogger,
    BuildManager,
    TowerBuiltEvent,
    DynamicRepathingSystem,
    SiegeSystem,
    SiegeComponent,
    TowerComponent,
    HealthComponent,
    TransformComponent,
    MovementComponent,
    HealthSystem,
    DeathSystem,
    EntityDeathEvent,
)


class TestSiegeComponent:
    """测试 SiegeComponent 攻城状态组件"""

    def setup_method(self):
        """每个测试方法前重置"""
        ServiceLocator.reset()
        EventBus.reset()

    def teardown_method(self):
        """每个测试方法后的清理"""
        ServiceLocator.reset()
        EventBus.reset()

    def test_default_constructor(self):
        """测试默认构造函数"""
        siege = SiegeComponent()
        
        assert siege.target_tower_id is None
        assert siege.target_tower_grid is None
        assert siege.attack_damage == 10.0
        assert siege.attack_interval == 1.0
        assert siege.cooldown_remaining == 0.0
        assert siege.is_active is False
        assert siege.has_target is False
        assert siege.is_ready is True

    def test_activate(self):
        """测试激活攻城状态"""
        siege = SiegeComponent()
        
        siege.activate(
            target_tower_id=5,
            target_tower_grid=(3, 2),
            attack_damage=15.0,
            attack_interval=0.5,
            destination_x=10.0,
            destination_y=0.0,
        )
        
        assert siege.is_active is True
        assert siege.has_target is True
        assert siege.target_tower_id == 5
        assert siege.target_tower_grid == (3, 2)
        assert siege.attack_damage == 15.0
        assert siege.attack_interval == 0.5
        assert siege.destination_x == 10.0
        assert siege.destination_y == 0.0

    def test_deactivate(self):
        """测试取消攻城状态"""
        siege = SiegeComponent()
        
        siege.activate(
            target_tower_id=5,
            target_tower_grid=(3, 2),
            attack_damage=15.0,
            attack_interval=0.5,
            destination_x=10.0,
            destination_y=0.0,
        )
        
        assert siege.is_active is True
        
        siege.deactivate()
        
        assert siege.is_active is False
        assert siege.has_target is False
        assert siege.target_tower_id is None
        assert siege.cooldown_remaining == 0.0

    def test_cooldown_management(self):
        """测试冷却时间管理"""
        siege = SiegeComponent()
        
        siege.activate(
            target_tower_id=5,
            target_tower_grid=(3, 2),
            attack_damage=15.0,
            attack_interval=1.0,
            destination_x=10.0,
            destination_y=0.0,
        )
        
        assert siege.is_ready is True
        
        siege.start_cooldown()
        assert siege.cooldown_remaining == 1.0
        assert siege.is_ready is False
        
        siege.update_cooldown(0.5)
        assert siege.cooldown_remaining == 0.5
        assert siege.is_ready is False
        
        siege.update_cooldown(0.6)
        assert siege.cooldown_remaining == 0.0
        assert siege.is_ready is True


class TestSiegeTrigger:
    """测试攻城状态触发（重寻路失败时）"""

    def setup_method(self):
        """每个测试方法前重置并注册必要服务"""
        ServiceLocator.reset()
        EventBus.reset()
        
        register_service(IDataLoader, MockDataLoader())
        register_service(IGameLogger, GameLogger())
        register_service(EntityManager, EntityManager())
        register_service(GridMap, GridMap(width=5, height=3))
        register_service(Pathfinder, Pathfinder())
        register_service(BuildManager, BuildManager())

    def teardown_method(self):
        """每个测试方法后的清理"""
        ServiceLocator.reset()
        EventBus.reset()

    def _create_enemy_with_path(
        self, 
        entity_manager: EntityManager,
        start_x: float, 
        start_y: float, 
        waypoints: List[tuple]
    ):
        """创建一个带有路径的敌人实体"""
        enemy = entity_manager.create_entity()
        
        transform = TransformComponent(x=start_x, y=start_y)
        enemy.add_component(transform)
        
        health = HealthComponent(current_health=100.0, max_health=100.0)
        enemy.add_component(health)
        
        movement = MovementComponent(
            speed=2.0,
            waypoints=waypoints,
            transform=transform
        )
        enemy.add_component(movement)
        
        return enemy, movement

    def test_path_completely_blocked_triggers_siege(self):
        """测试路径被彻底堵死时触发攻城状态"""
        entity_manager = get_service(EntityManager)
        grid_map = get_service(GridMap)
        build_manager = get_service(BuildManager)
        
        enemy, movement = self._create_enemy_with_path(
            entity_manager, 
            start_x=0.0, 
            start_y=1.0,
            waypoints=[(1.0, 1.0), (2.0, 1.0), (3.0, 1.0), (4.0, 1.0)]
        )
        
        tower1 = build_manager.build_tower("tower_arrow_001", 2, 1)
        assert tower1 is not None
        assert grid_map.is_walkable(2, 1) is False
        
        tower2 = build_manager.build_tower("tower_arrow_001", 2, 0)
        tower3 = build_manager.build_tower("tower_arrow_001", 2, 2)
        
        tower1_health = tower1.get_component(HealthComponent)
        assert tower1_health is not None
        assert tower1_health.current_health == tower1_health.max_health
        
        system = DynamicRepathingSystem()
        
        is_affected = system._check_and_repath(enemy, 2, 1, grid_map)
        
        assert is_affected is False
        
        siege_comp = enemy.get_component(SiegeComponent)
        assert siege_comp is not None
        assert siege_comp.is_active is True
        assert siege_comp.target_tower_id is not None

    def test_find_nearest_blocking_tower(self):
        """测试寻找最近的阻挡防御塔"""
        entity_manager = get_service(EntityManager)
        grid_map = get_service(GridMap)
        build_manager = get_service(BuildManager)
        
        tower1 = build_manager.build_tower("tower_arrow_001", 2, 0)
        tower2 = build_manager.build_tower("tower_arrow_001", 5, 0)
        
        enemy = entity_manager.create_entity()
        enemy.add_component(TransformComponent(x=0.0, y=0.0))
        enemy.add_component(HealthComponent(current_health=100.0, max_health=100.0))
        
        system = DynamicRepathingSystem()
        
        nearest = system._find_nearest_blocking_tower(
            entity_manager, grid_map, 0, 0
        )
        
        assert nearest is not None
        tower_entity, tower_grid = nearest
        assert tower_entity.entity_id == tower1.entity_id
        assert tower_grid == (2, 0)


class TestSiegeSystem:
    """测试 SiegeSystem 攻城状态系统"""

    def setup_method(self):
        """每个测试方法前重置并注册必要服务"""
        ServiceLocator.reset()
        EventBus.reset()
        
        register_service(IDataLoader, MockDataLoader())
        register_service(IGameLogger, GameLogger())
        register_service(EntityManager, EntityManager())
        register_service(GridMap, GridMap(width=5, height=3))
        register_service(Pathfinder, Pathfinder())
        register_service(BuildManager, BuildManager())
        register_service(HealthSystem, HealthSystem())

    def teardown_method(self):
        """每个测试方法后的清理"""
        ServiceLocator.reset()
        EventBus.reset()

    def _create_tower(self, grid_x: int, grid_y: int, max_health: float = 50.0):
        """创建一个防御塔"""
        entity_manager = get_service(EntityManager)
        grid_map = get_service(GridMap)
        
        tower = entity_manager.create_entity()
        
        transform = TransformComponent(x=float(grid_x), y=float(grid_y))
        tower.add_component(transform)
        
        tower_comp = TowerComponent(
            config_id="tower_test",
            name="Test Tower",
            cost=100,
            damage=20,
            attack_range=3.0,
            attack_speed=1.0,
        )
        tower.add_component(tower_comp)
        
        health = HealthComponent(current_health=max_health, max_health=max_health)
        tower.add_component(health)
        
        grid_map.set_walkable(grid_x, grid_y, False)
        
        return tower

    def _create_enemy_in_siege_state(
        self,
        start_x: float,
        start_y: float,
        target_tower,
        attack_damage: float = 10.0,
        attack_interval: float = 1.0,
        destination_x: float = 9.0,
        destination_y: float = 0.0,
    ):
        """创建一个处于攻城状态的敌人"""
        entity_manager = get_service(EntityManager)
        
        enemy = entity_manager.create_entity()
        
        transform = TransformComponent(x=start_x, y=start_y)
        enemy.add_component(transform)
        
        health = HealthComponent(current_health=100.0, max_health=100.0)
        enemy.add_component(health)
        
        movement = MovementComponent(
            speed=2.0,
            waypoints=[],
            transform=transform
        )
        enemy.add_component(movement)
        
        tower_transform = target_tower.get_component(TransformComponent)
        tower_grid_x = int(tower_transform.x)
        tower_grid_y = int(tower_transform.y)
        
        siege = SiegeComponent()
        siege.activate(
            target_tower_id=target_tower.entity_id,
            target_tower_grid=(tower_grid_x, tower_grid_y),
            attack_damage=attack_damage,
            attack_interval=attack_interval,
            destination_x=destination_x,
            destination_y=destination_y,
        )
        enemy.add_component(siege)
        
        return enemy, siege

    def test_siege_system_initialize_shutdown(self):
        """测试攻城系统的初始化和关闭"""
        system = SiegeSystem()
        
        assert system.is_initialized() is False
        
        system.initialize()
        assert system.is_initialized() is True
        
        system.shutdown()
        assert system.is_initialized() is False

    def test_siege_enemy_attacks_tower(self):
        """测试处于攻城状态的敌人攻击防御塔"""
        entity_manager = get_service(EntityManager)
        grid_map = get_service(GridMap)
        health_system = get_service(HealthSystem)
        
        tower = self._create_tower(3, 0, max_health=50.0)
        tower_health = tower.get_component(HealthComponent)
        
        enemy, siege = self._create_enemy_in_siege_state(
            start_x=2.0,
            start_y=0.0,
            target_tower=tower,
            attack_damage=15.0,
            attack_interval=1.0,
        )
        
        assert tower_health.current_health == 50.0
        assert siege.cooldown_remaining == 0.0
        assert siege.is_ready is True
        
        system = SiegeSystem()
        system.initialize()
        
        system.tick(delta=0.1)
        
        assert tower_health.current_health == 35.0
        assert siege.cooldown_remaining == 1.0
        assert siege.is_ready is False
        
        system.tick(delta=0.5)
        assert siege.cooldown_remaining == 0.5
        assert siege.is_ready is False
        assert tower_health.current_health == 35.0
        
        system.tick(delta=0.6)
        assert tower_health.current_health == 20.0
        assert siege.cooldown_remaining == 1.0
        assert siege.is_ready is False
        
        system.tick(delta=1.1)
        assert tower_health.current_health == 5.0
        assert siege.cooldown_remaining == 1.0
        assert siege.is_ready is False

    def test_tower_destroyed_restores_walkable(self):
        """测试塔被摧毁后恢复网格可通行性"""
        entity_manager = get_service(EntityManager)
        grid_map = get_service(GridMap)
        health_system = get_service(HealthSystem)
        
        tower = self._create_tower(3, 0, max_health=30.0)
        tower_id = tower.entity_id
        tower_health = tower.get_component(HealthComponent)
        
        assert grid_map.is_walkable(3, 0) is False
        
        death_system = DeathSystem()
        death_system.initialize()
        
        health_system.take_damage(tower, 30.0)
        
        assert tower_health.current_health <= 0.0
        
        assert grid_map.is_walkable(3, 0) is True
        
        death_system.shutdown()


class TestIntegration:
    """测试攻城模式的完整集成流程"""

    def setup_method(self):
        """每个测试方法前重置并注册必要服务"""
        ServiceLocator.reset()
        EventBus.reset()
        
        register_service(IDataLoader, MockDataLoader())
        register_service(IGameLogger, GameLogger())
        register_service(EntityManager, EntityManager())
        register_service(GridMap, GridMap(width=5, height=3))
        register_service(Pathfinder, Pathfinder())
        register_service(BuildManager, BuildManager())
        register_service(HealthSystem, HealthSystem())

    def teardown_method(self):
        """每个测试方法后的清理"""
        ServiceLocator.reset()
        EventBus.reset()

    def test_full_siege_flow(self):
        """测试完整的攻城流程：堵路 -> 攻城 -> 摧毁塔 -> 重寻路"""
        entity_manager = get_service(EntityManager)
        grid_map = get_service(GridMap)
        build_manager = get_service(BuildManager)
        health_system = get_service(HealthSystem)
        
        grid_map.set_walkable(2, 0, False)
        grid_map.set_walkable(2, 2, False)
        
        enemy = entity_manager.create_entity()
        transform = TransformComponent(x=1.0, y=1.0)
        enemy.add_component(transform)
        enemy.add_component(HealthComponent(current_health=100.0, max_health=100.0))
        movement = MovementComponent(
            speed=2.0,
            waypoints=[(2.0, 1.0), (3.0, 1.0), (4.0, 1.0)],
            transform=transform
        )
        enemy.add_component(movement)
        
        tower = build_manager.build_tower("tower_arrow_001", 2, 1)
        assert tower is not None
        tower_health = tower.get_component(HealthComponent)
        assert tower_health is not None
        
        death_system = DeathSystem()
        death_system.initialize()
        
        repathing_system = DynamicRepathingSystem()
        
        is_affected = repathing_system._check_and_repath(enemy, 2, 1, grid_map)
        
        assert is_affected is False
        
        siege_comp = enemy.get_component(SiegeComponent)
        assert siege_comp is not None
        assert siege_comp.is_active is True
        assert siege_comp.target_tower_id == tower.entity_id
        
        siege_system = SiegeSystem()
        siege_system.initialize()
        
        siege_system.tick(delta=0.1)
        
        assert tower_health.current_health < tower_health.max_health
        
        remaining = tower_health.current_health
        while remaining > 0:
            siege_comp.cooldown_remaining = 0.0
            siege_system.tick(delta=0.1)
            remaining = tower_health.current_health
        
        assert tower_health.current_health <= 0.0
        
        assert grid_map.is_walkable(2, 1) is True
        
        siege_comp.cooldown_remaining = 0.0
        siege_system.tick(delta=0.1)
        
        assert siege_comp.is_active is False
        
        death_system.shutdown()
        siege_system.shutdown()
