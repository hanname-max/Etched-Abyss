"""
MovementComponent 测试

测试 MovementComponent 的路径移动功能。
"""

import pytest
from collections import deque

from CoreLogic import (
    TransformComponent,
    MovementComponent,
    EntityManager,
    ServiceLocator,
    EventBus,
)


class TestMovementComponent:
    """MovementComponent 测试"""
    
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
        movement = MovementComponent()
        assert movement.speed == 1.0
        assert movement.waypoints == deque()
        assert movement.transform is None
        assert movement.reached_end is False
        assert movement.has_waypoints is False
    
    def test_parameterized_constructor(self):
        """测试带参数构造函数"""
        transform = TransformComponent(x=0.0, y=0.0)
        movement = MovementComponent(
            speed=3.0,
            waypoints=[(1.0, 0.0), (2.0, 1.0)],
            transform=transform
        )
        assert movement.speed == 3.0
        assert movement.has_waypoints is True
        assert movement.transform is transform
        assert movement.reached_end is False
    
    def test_waypoints_converted_to_deque(self):
        """测试路径点列表自动转换为 deque"""
        movement = MovementComponent(waypoints=[(1.0, 2.0), (3.0, 4.0)])
        assert isinstance(movement.waypoints, deque)
        assert len(movement.waypoints) == 2
        assert movement.waypoints[0] == (1.0, 2.0)
        assert movement.waypoints[1] == (3.0, 4.0)
    
    def test_add_waypoint(self):
        """测试添加单个路径点"""
        movement = MovementComponent()
        assert movement.has_waypoints is False
        
        movement.add_waypoint(5.0, 10.0)
        assert movement.has_waypoints is True
        assert len(movement.waypoints) == 1
        assert movement.waypoints[0] == (5.0, 10.0)
        
        movement.add_waypoint(15.0, 20.0)
        assert len(movement.waypoints) == 2
    
    def test_add_waypoints(self):
        """测试批量添加路径点"""
        movement = MovementComponent()
        
        points = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
        movement.add_waypoints(points)
        
        assert len(movement.waypoints) == 3
        assert movement.waypoints[0] == (0.0, 0.0)
        assert movement.waypoints[1] == (1.0, 0.0)
        assert movement.waypoints[2] == (1.0, 1.0)
    
    def test_clear_waypoints(self):
        """测试清空路径点"""
        movement = MovementComponent(waypoints=[(1.0, 1.0), (2.0, 2.0)])
        assert movement.has_waypoints is True
        
        movement.clear_waypoints()
        assert movement.has_waypoints is False
        assert len(movement.waypoints) == 0
    
    def test_update_without_transform_does_nothing(self):
        """测试没有 transform 引用时 update 不做任何事"""
        movement = MovementComponent(
            speed=2.0,
            waypoints=[(5.0, 0.0)]
        )
        original_waypoints = list(movement.waypoints)
        
        movement.update(delta=1.0)
        
        assert list(movement.waypoints) == original_waypoints
        assert movement.reached_end is False
    
    def test_update_moves_towards_target(self):
        """测试更新时向目标点移动"""
        transform = TransformComponent(x=0.0, y=0.0)
        movement = MovementComponent(
            speed=2.0,
            waypoints=[(10.0, 0.0)],
            transform=transform
        )
        
        movement.update(delta=1.0)
        
        assert transform.x == 2.0
        assert transform.y == 0.0
        assert movement.has_waypoints is True
        assert movement.reached_end is False
    
    def test_update_reaches_target(self):
        """测试到达目标点后弹出路径点"""
        transform = TransformComponent(x=0.0, y=0.0)
        movement = MovementComponent(
            speed=5.0,
            waypoints=[(10.0, 0.0)],
            transform=transform
        )
        
        movement.update(delta=2.0)
        
        assert transform.x == 10.0
        assert transform.y == 0.0
        assert movement.has_waypoints is False
        assert movement.reached_end is True
    
    def test_update_with_multiple_waypoints(self):
        """测试多个路径点的顺序移动"""
        transform = TransformComponent(x=0.0, y=0.0)
        movement = MovementComponent(
            speed=2.0,
            waypoints=[(2.0, 0.0), (2.0, 2.0), (0.0, 2.0)],
            transform=transform
        )
        
        movement.update(delta=1.0)
        assert transform.x == 2.0
        assert transform.y == 0.0
        assert len(movement.waypoints) == 2
        assert movement.waypoints[0] == (2.0, 2.0)
        
        movement.update(delta=1.0)
        assert transform.x == 2.0
        assert transform.y == 2.0
        assert len(movement.waypoints) == 1
        assert movement.waypoints[0] == (0.0, 2.0)
        
        movement.update(delta=1.0)
        assert transform.x == 0.0
        assert transform.y == 2.0
        assert movement.has_waypoints is False
        assert movement.reached_end is True
    
    def test_update_with_diagonal_movement(self):
        """测试对角线移动"""
        transform = TransformComponent(x=0.0, y=0.0)
        movement = MovementComponent(
            speed=1.0,
            waypoints=[(3.0, 4.0)],
            transform=transform
        )
        
        movement.update(delta=5.0)
        
        assert transform.x == 3.0
        assert transform.y == 4.0
        assert movement.reached_end is True
    
    def test_update_with_epsilon_distance(self):
        """测试极小距离时的精确到达"""
        transform = TransformComponent(x=0.0, y=0.0)
        movement = MovementComponent(
            speed=1.0,
            waypoints=[(0.005, 0.005)],
            transform=transform
        )
        
        movement.update(delta=0.01)
        
        assert transform.x == 0.005
        assert transform.y == 0.005
        assert movement.reached_end is True
    
    def test_update_after_reached_end_does_nothing(self):
        """测试到达终点后再次调用 update 不做任何事"""
        transform = TransformComponent(x=0.0, y=0.0)
        movement = MovementComponent(
            speed=2.0,
            waypoints=[(1.0, 0.0)],
            transform=transform
        )
        
        movement.update(delta=1.0)
        assert movement.reached_end is True
        assert transform.x == 1.0
        
        movement.update(delta=1.0)
        assert transform.x == 1.0
        assert movement.reached_end is True
    
    def test_add_waypoint_after_reached_end_resets(self):
        """测试到达终点后添加新路径点会重置状态"""
        transform = TransformComponent(x=0.0, y=0.0)
        movement = MovementComponent(
            speed=2.0,
            waypoints=[(1.0, 0.0)],
            transform=transform
        )
        
        movement.update(delta=1.0)
        assert movement.reached_end is True
        
        movement.add_waypoint(2.0, 0.0)
        assert movement.reached_end is False
        assert movement.has_waypoints is True
        
        movement.update(delta=0.5)
        assert transform.x == 2.0
        assert movement.reached_end is True


class TestMovementComponentWithEntityManager:
    """MovementComponent 与 EntityManager 集成测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        ServiceLocator.reset()
        EventBus.reset()
        self.em = EntityManager()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
        EventBus.reset()
    
    def test_entity_manager_tick_calls_update(self):
        """测试 EntityManager.tick 自动调用 MovementComponent.update"""
        entity = self.em.create_entity()
        transform = TransformComponent(x=0.0, y=0.0)
        movement = MovementComponent(
            speed=2.0,
            waypoints=[(10.0, 0.0)],
            transform=transform
        )
        
        entity.add_component(transform)
        entity.add_component(movement)
        
        self.em.tick(delta=1.0)
        
        assert transform.x == 2.0
        assert transform.y == 0.0
    
    def test_full_path_following_in_entity_manager(self):
        """测试在 EntityManager 中完整的路径跟随"""
        entity = self.em.create_entity()
        transform = TransformComponent(x=0.0, y=0.0)
        movement = MovementComponent(
            speed=2.0,
            waypoints=[(2.0, 0.0), (2.0, 2.0), (0.0, 2.0)],
            transform=transform
        )
        
        entity.add_component(transform)
        entity.add_component(movement)
        
        self.em.tick(delta=1.0)
        assert (transform.x, transform.y) == (2.0, 0.0)
        assert movement.reached_end is False
        
        self.em.tick(delta=1.0)
        assert (transform.x, transform.y) == (2.0, 2.0)
        assert movement.reached_end is False
        
        self.em.tick(delta=1.0)
        assert (transform.x, transform.y) == (0.0, 2.0)
        assert movement.reached_end is True
    
    def test_multiple_entities_with_movement(self):
        """测试多个实体同时移动"""
        entity1 = self.em.create_entity()
        transform1 = TransformComponent(x=0.0, y=0.0)
        movement1 = MovementComponent(
            speed=1.0,
            waypoints=[(5.0, 0.0)],
            transform=transform1
        )
        entity1.add_component(transform1)
        entity1.add_component(movement1)
        
        entity2 = self.em.create_entity()
        transform2 = TransformComponent(x=0.0, y=0.0)
        movement2 = MovementComponent(
            speed=2.0,
            waypoints=[(5.0, 0.0)],
            transform=transform2
        )
        entity2.add_component(transform2)
        entity2.add_component(movement2)
        
        self.em.tick(delta=1.0)
        
        assert transform1.x == 1.0
        assert transform2.x == 2.0
