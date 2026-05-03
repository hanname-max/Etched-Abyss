"""
动态重寻路系统单元测试

测试 DynamicRepathingSystem 的核心功能，包括：
1. TowerBuiltEvent 事件的发布和接收
2. 敌人路径被阻断时的检测
3. 重新寻路逻辑
4. 路径更新
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
    HealthComponent,
    TransformComponent,
    MovementComponent,
)


class TestTowerBuiltEvent:
    """测试 TowerBuiltEvent 事件"""

    def setup_method(self):
        """每个测试方法前重置 EventBus 和 ServiceLocator"""
        ServiceLocator.reset()
        EventBus.reset()

    def test_tower_built_event_creation(self):
        """测试 TowerBuiltEvent 的创建"""
        event = TowerBuiltEvent(
            tower_entity_id=1,
            grid_x=5,
            grid_y=3,
            tower_config_id="tower_arrow_001"
        )
        
        assert event.tower_entity_id == 1
        assert event.grid_x == 5
        assert event.grid_y == 3
        assert event.tower_config_id == "tower_arrow_001"

    def test_tower_built_event_publish_and_subscribe(self):
        """测试 TowerBuiltEvent 的发布和订阅"""
        received_events: List[TowerBuiltEvent] = []
        
        def on_tower_built(event: TowerBuiltEvent) -> None:
            received_events.append(event)
        
        subscribe(TowerBuiltEvent, on_tower_built)
        
        event = TowerBuiltEvent(
            tower_entity_id=1,
            grid_x=5,
            grid_y=3,
            tower_config_id="tower_arrow_001"
        )
        publish(event)
        
        assert len(received_events) == 1
        assert received_events[0].tower_entity_id == 1
        assert received_events[0].grid_x == 5
        
        unsubscribe(TowerBuiltEvent, on_tower_built)
        
        publish(TowerBuiltEvent(
            tower_entity_id=2,
            grid_x=2,
            grid_y=2,
            tower_config_id="tower_cannon_001"
        ))
        
        assert len(received_events) == 1


class TestDynamicRepathingSystem:
    """测试动态重寻路系统"""

    def setup_method(self):
        """每个测试方法前重置并注册必要服务"""
        ServiceLocator.reset()
        EventBus.reset()
        
        register_service(IDataLoader, MockDataLoader())
        register_service(IGameLogger, GameLogger())
        register_service(EntityManager, EntityManager())
        register_service(GridMap, GridMap(width=10, height=10))
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
        """
        创建一个带有路径的敌人实体。
        
        返回：
            (enemy_entity, movement_component)
        """
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

    def test_system_enable_disable(self):
        """测试系统的启用和禁用"""
        system = DynamicRepathingSystem()
        
        assert system.is_enabled is False
        
        system.enable()
        assert system.is_enabled is True
        
        system.disable()
        assert system.is_enabled is False

    def test_is_path_blocked_detection(self):
        """测试路径被阻断的检测逻辑"""
        system = DynamicRepathingSystem()
        
        waypoints = deque([(1.0, 0.0), (2.0, 0.0), (3.0, 0.0), (4.0, 0.0)])
        
        assert system._is_path_blocked(waypoints, 2, 0) is True
        assert system._is_path_blocked(waypoints, 5, 0) is False
        assert system._is_path_blocked(waypoints, 2, 1) is False

    def test_is_path_blocked_with_float_coordinates(self):
        """测试浮点数路径点的阻断检测"""
        system = DynamicRepathingSystem()
        
        waypoints = deque([(1.5, 0.0), (2.0, 0.0), (2.5, 0.0)])
        
        assert system._is_path_blocked(waypoints, 2, 0) is True
        assert system._is_path_blocked(waypoints, 1, 0) is False
        assert system._is_path_blocked(waypoints, 3, 0) is False

    def test_prepare_waypoints_removes_start_if_same(self):
        """测试路径点准备时移除与当前位置相同的起点"""
        system = DynamicRepathingSystem()
        
        path = [(0, 0), (1, 0), (2, 0)]
        transform = TransformComponent(x=0.0, y=0.0)
        
        prepared = system._prepare_waypoints(path, transform)
        
        assert len(prepared) == 2
        assert prepared[0] == (1.0, 0.0)
        assert prepared[1] == (2.0, 0.0)

    def test_prepare_waypoints_keeps_start_if_different(self):
        """测试路径点准备时保留与当前位置不同的起点"""
        system = DynamicRepathingSystem()
        
        path = [(1, 0), (2, 0), (3, 0)]
        transform = TransformComponent(x=0.0, y=0.0)
        
        prepared = system._prepare_waypoints(path, transform)
        
        assert len(prepared) == 3
        assert prepared[0] == (1.0, 0.0)

    def test_get_alive_enemies(self):
        """测试获取存活敌人"""
        entity_manager = get_service(EntityManager)
        
        enemy1, _ = self._create_enemy_with_path(
            entity_manager, 0.0, 0.0, [(1.0, 0.0), (2.0, 0.0)]
        )
        
        enemy2, _ = self._create_enemy_with_path(
            entity_manager, 5.0, 5.0, [(6.0, 5.0), (7.0, 5.0)]
        )
        health2 = enemy2.get_component(HealthComponent)
        health2.current_health = 0.0
        
        tower = entity_manager.create_entity()
        tower.add_component(TransformComponent(x=3.0, y=3.0))
        
        system = DynamicRepathingSystem()
        alive_enemies = system._get_alive_enemies(entity_manager)
        
        assert len(alive_enemies) == 1
        assert alive_enemies[0].entity_id == enemy1.entity_id

    def test_enemy_path_blocked_triggers_repath(self):
        """测试敌人路径被阻断时触发重新寻路"""
        entity_manager = get_service(EntityManager)
        grid_map = get_service(GridMap)
        
        enemy, movement = self._create_enemy_with_path(
            entity_manager, 
            start_x=0.0, 
            start_y=0.0,
            waypoints=[(1.0, 0.0), (2.0, 0.0), (3.0, 0.0), (4.0, 0.0)]
        )
        
        original_waypoints = list(movement.waypoints)
        assert len(original_waypoints) == 4
        
        grid_map.set_walkable(2, 0, False)
        
        system = DynamicRepathingSystem()
        
        is_affected = system._check_and_repath(enemy, 2, 0, grid_map)
        
        assert is_affected is True
        
        new_waypoints = list(movement.waypoints)
        for wp in new_waypoints:
            wx, wy = wp
            assert not (abs(wx - 2.0) < 0.01 and abs(wy - 0.0) < 0.01)

    def test_system_receives_tower_built_event(self):
        """测试系统接收 TowerBuiltEvent 事件"""
        entity_manager = get_service(EntityManager)
        grid_map = get_service(GridMap)
        
        enemy, movement = self._create_enemy_with_path(
            entity_manager, 
            start_x=0.0, 
            start_y=0.0,
            waypoints=[(1.0, 0.0), (2.0, 0.0), (3.0, 0.0), (4.0, 0.0)]
        )
        
        original_waypoints = list(movement.waypoints)
        
        system = DynamicRepathingSystem()
        system.enable()
        
        build_manager = get_service(BuildManager)
        tower = build_manager.build_tower("tower_arrow_001", 2, 0)
        
        assert tower is not None
        assert grid_map.is_walkable(2, 0) is False
        
        system.disable()

    def test_dead_enemy_not_affected(self):
        """测试死亡的敌人不会被影响"""
        entity_manager = get_service(EntityManager)
        grid_map = get_service(GridMap)
        
        enemy, movement = self._create_enemy_with_path(
            entity_manager, 
            start_x=0.0, 
            start_y=0.0,
            waypoints=[(1.0, 0.0), (2.0, 0.0), (3.0, 0.0)]
        )
        
        health = enemy.get_component(HealthComponent)
        health.current_health = 0.0
        
        original_waypoints = list(movement.waypoints)
        
        grid_map.set_walkable(2, 0, False)
        
        system = DynamicRepathingSystem()
        
        is_affected = system._check_and_repath(enemy, 2, 0, grid_map)
        
        assert is_affected is False
        assert list(movement.waypoints) == original_waypoints

    def test_enemy_without_waypoints_not_affected(self):
        """测试没有路径点的敌人不会被影响"""
        entity_manager = get_service(EntityManager)
        grid_map = get_service(GridMap)
        
        enemy, movement = self._create_enemy_with_path(
            entity_manager, 
            start_x=0.0, 
            start_y=0.0,
            waypoints=[]
        )
        
        grid_map.set_walkable(2, 0, False)
        
        system = DynamicRepathingSystem()
        
        is_affected = system._check_and_repath(enemy, 2, 0, grid_map)
        
        assert is_affected is False
