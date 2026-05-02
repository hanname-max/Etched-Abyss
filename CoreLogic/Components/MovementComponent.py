"""
移动组件

MovementComponent 用于控制实体沿着预设路径点移动。

============================================================================
【架构说明】
============================================================================

此组件实现了 IUpdateable 接口，用于自驱动的路径移动。
与纯数据组件不同，此组件在 update 中会直接修改关联的 TransformComponent。

使用方式：
    transform = TransformComponent(x=0, y=0)
    movement = MovementComponent(
        speed=2.0,
        waypoints=[(5.0, 5.0), (10.0, 0.0)],
        transform=transform
    )
    entity.add_component(transform)
    entity.add_component(movement)

    # EntityManager.tick 会自动调用 movement.update(delta)
    # transform 的位置会自动更新
============================================================================
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Tuple, Optional

from CoreLogic.Interfaces.IUpdateable import IUpdateable
from CoreLogic.Components.TransformComponent import TransformComponent
from CoreLogic.Core.ServiceLocator import try_get_service
from CoreLogic.Interfaces.IGameLogger import IGameLogger


@dataclass
class MovementComponent(IUpdateable):
    """
    移动组件，控制实体沿着预设路径点移动。
    
    此组件实现了 IUpdateable 接口，需要与 TransformComponent 配合使用。
    EntityManager.tick 会自动调用 update 方法，使实体沿着路径点移动。
    
    属性：
        speed: 移动速度（单位/秒）
        waypoints: 路径点队列，存储 (x, y) 坐标元组
        transform: 关联的 TransformComponent 引用，用于更新位置
        _reached_end: 私有标记，表示是否已到达终点
        _logged_end: 私有标记，表示是否已打印到达终点的日志
    
    使用示例：
        transform = TransformComponent(x=0, y=0)
        movement = MovementComponent(
            speed=3.0,
            waypoints=[(2.0, 0.0), (2.0, 2.0), (0.0, 2.0)],
            transform=transform
        )
        
        entity.add_component(transform)
        entity.add_component(movement)
        
        # 每帧调用 update（由 EntityManager 自动处理）
        movement.update(delta=0.5)
        
        # 检查是否到达终点
        if movement.reached_end:
            print("敌人已到达终点!")
    """
    
    speed: float = 1.0
    waypoints: Deque[Tuple[float, float]] = field(default_factory=deque)
    transform: Optional[TransformComponent] = None
    _reached_end: bool = field(default=False, repr=False)
    _logged_end: bool = field(default=False, repr=False)
    
    def __post_init__(self) -> None:
        """
        初始化后处理。
        确保 waypoints 是 deque 类型。
        """
        if not isinstance(self.waypoints, deque):
            if isinstance(self.waypoints, list):
                self.waypoints = deque(self.waypoints)
            else:
                self.waypoints = deque()
    
    @property
    def reached_end(self) -> bool:
        """
        是否已到达终点。
        
        返回：
            True 如果路径点队列为空且已到达最后一个目标点
        """
        return self._reached_end
    
    @property
    def has_waypoints(self) -> bool:
        """
        是否还有未完成的路径点。
        
        返回：
            True 如果路径点队列不为空
        """
        return len(self.waypoints) > 0
    
    def add_waypoint(self, x: float, y: float) -> None:
        """
        添加一个路径点到队列末尾。

        参数：
            x: 目标 X 坐标
            y: 目标 Y 坐标
        """
        self.waypoints.append((x, y))
        self._reached_end = False
        self._logged_end = False
    
    def add_waypoints(self, points: list) -> None:
        """
        批量添加路径点。
        
        参数：
            points: 坐标列表，如 [(x1, y1), (x2, y2), ...]
        """
        for x, y in points:
            self.waypoints.append((x, y))
        self._reached_end = False
        self._logged_end = False
    
    def clear_waypoints(self) -> None:
        """
        清空所有路径点。
        """
        self.waypoints.clear()
        self._reached_end = False
        self._logged_end = False
    
    def update(self, delta: float) -> None:
        """
        每帧更新方法，实现 IUpdateable 接口。
        
        由 EntityManager.tick 自动调用。
        
        更新逻辑：
        1. 如果没有 transform 引用或已到达终点，直接返回
        2. 如果路径点队列为空，标记为已到达终点并打印日志
        3. 否则，计算向第一个路径点的插值移动
        4. 当距离极小时（< 0.01），弹出路径点
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
        """
        if self.transform is None:
            return
        
        if self._reached_end:
            return
        
        if not self.waypoints:
            self._reached_end = True
            self._log_reached_end()
            return
        
        target_x, target_y = self.waypoints[0]
        current_x = self.transform.x
        current_y = self.transform.y
        
        dx = target_x - current_x
        dy = target_y - current_y
        
        distance_squared = dx * dx + dy * dy
        epsilon = 0.01
        epsilon_squared = epsilon * epsilon
        
        if distance_squared < epsilon_squared:
            self.transform.x = target_x
            self.transform.y = target_y
            self.waypoints.popleft()
            
            if not self.waypoints:
                self._reached_end = True
                self._log_reached_end()
            return
        
        distance = distance_squared ** 0.5
        max_move_distance = self.speed * delta
        
        if max_move_distance >= distance:
            self.transform.x = target_x
            self.transform.y = target_y
            self.waypoints.popleft()
            
            if not self.waypoints:
                self._reached_end = True
                self._log_reached_end()
        else:
            ratio = max_move_distance / distance
            self.transform.x += dx * ratio
            self.transform.y += dy * ratio
    
    def _log_reached_end(self) -> None:
        """
        打印到达终点的日志。
        使用 ServiceLocator 获取 IGameLogger 进行日志输出。
        """
        if self._logged_end:
            return
        self._logged_end = True
        
        logger = try_get_service(IGameLogger)
        if logger is not None:
            logger.info("MovementComponent: Entity reached end of path", 
                       position=(self.transform.x if self.transform else 0, 
                                self.transform.y if self.transform else 0))
