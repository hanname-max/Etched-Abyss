"""
追踪移动组件

HomingMovementComponent 用于控制投射物追踪目标敌人飞行。

============================================================================
【架构说明】
============================================================================

此组件实现了 IUpdateable 接口，用于自驱动的追踪移动。
与 MovementComponent 类似，这是一个有意识的设计选择，
用于简化投射物的追踪飞行逻辑。

使用方式：
    transform = TransformComponent(x=5.0, y=3.0)
    projectile = ProjectileComponent(
        damage=25.0,
        target_id=5,
        hit_threshold=0.1
    )
    homing = HomingMovementComponent(
        speed=8.0,
        target_id=5,
        projectile_id=10,
        transform=transform,
        projectile_component=projectile
    )
    entity.add_component(transform)
    entity.add_component(projectile)
    entity.add_component(homing)

    # EntityManager.tick 会自动调用 homing.update(delta)
    # 投射物会自动追踪目标，击中时发布 ProjectileHitEvent 并销毁
============================================================================
"""

from dataclasses import dataclass, field
from typing import Optional

from CoreLogic.Interfaces.IUpdateable import IUpdateable
from CoreLogic.Components.TransformComponent import TransformComponent
from CoreLogic.Components.ProjectileComponent import ProjectileComponent
from CoreLogic.Components.HealthComponent import HealthComponent
from CoreLogic.Managers.EntityManager import EntityManager
from CoreLogic.Core.ServiceLocator import try_get_service
from CoreLogic.Core.EventBus import publish
from CoreLogic.Events.ProjectileHitEvent import ProjectileHitEvent
from CoreLogic.Interfaces.IGameLogger import IGameLogger


@dataclass
class HomingMovementComponent(IUpdateable):
    """
    追踪移动组件，控制投射物追踪目标敌人飞行。
    
    此组件实现了 IUpdateable 接口，需要与 TransformComponent 和
    ProjectileComponent 配合使用。EntityManager.tick 会自动调用
    update 方法，使投射物追踪目标敌人飞行。
    
    核心逻辑：
    1. 每帧获取目标敌人的最新坐标
    2. 计算方向向量并向目标移动
    3. 检测与目标的距离，如果小于阈值则判定为击中
    4. 击中时发布 ProjectileHitEvent 并标记投射物为非活动状态
    
    属性：
        speed: 飞行速度（单位/秒）
        target_id: 目标敌人实体 ID
        projectile_id: 投射物自身实体 ID（用于发布击中事件）
        transform: 关联的 TransformComponent 引用，用于获取和更新位置
        projectile_component: 关联的 ProjectileComponent 引用
        _has_hit: 私有标记，表示是否已击中目标
        _target_lost: 私有标记，表示目标是否已丢失（如目标死亡）
    
    使用示例：
        # 创建投射物实体
        projectile_entity = entity_manager.create_entity()
        projectile_transform = TransformComponent(x=5.0, y=3.0)
        projectile_comp = ProjectileComponent(
            damage=25.0,
            target_id=enemy_id,
            hit_threshold=0.1
        )
        homing = HomingMovementComponent(
            speed=8.0,
            target_id=enemy_id,
            projectile_id=projectile_entity.entity_id,
            transform=projectile_transform,
            projectile_component=projectile_comp
        )
        projectile_entity.add_component(projectile_transform)
        projectile_entity.add_component(projectile_comp)
        projectile_entity.add_component(homing)
        
        # 每帧更新后，投射物会自动追踪目标
        entity_manager.tick(delta=0.1)
    """
    
    speed: float
    target_id: int
    projectile_id: int
    transform: Optional[TransformComponent] = None
    projectile_component: Optional[ProjectileComponent] = None
    _has_hit: bool = field(default=False, repr=False)
    _target_lost: bool = field(default=False, repr=False)
    
    @property
    def is_active(self) -> bool:
        """
        投射物是否仍处于活动状态。
        
        返回：
            True 如果未击中目标且目标未丢失
        """
        return not self._has_hit and not self._target_lost
    
    def _get_logger(self) -> Optional[IGameLogger]:
        """
        从 ServiceLocator 获取日志器。
        
        返回：
            如果已注册，返回 IGameLogger 实例；否则返回 None
        """
        return try_get_service(IGameLogger)
    
    def _log_projectile(self, message: str, **kwargs) -> None:
        """
        记录投射物相关日志。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数
        """
        logger = self._get_logger()
        if logger is not None:
            logger.info(message, **kwargs)
    
    def update(self, delta: float) -> None:
        """
        每帧更新方法，实现 IUpdateable 接口。
        
        由 EntityManager.tick 自动调用。
        
        更新逻辑：
        1. 如果已击中目标或目标已丢失，直接返回
        2. 验证必要的组件引用是否存在
        3. 通过 EntityManager 获取目标敌人
        4. 如果目标不存在或已死亡，标记为目标丢失
        5. 计算当前位置与目标位置的方向向量
        6. 根据速度和 delta 计算移动距离
        7. 更新投射物位置
        8. 检测与目标的距离，如果小于阈值则判定为击中
        9. 击中时：
           - 发布 ProjectileHitEvent
           - 标记为已击中
           - 标记 ProjectileComponent.is_active = False
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
        """
        if not self.is_active:
            return
        
        if self.transform is None or self.projectile_component is None:
            return
        
        if delta < 0:
            delta = 0.0
        
        entity_manager = try_get_service(EntityManager)
        if entity_manager is None:
            return
        
        target_entity = entity_manager.get_entity(self.target_id)
        
        if target_entity is None:
            self._target_lost = True
            self._log_projectile(
                "投射物目标丢失：目标实体不存在",
                projectile_id=self.projectile_id,
                target_id=self.target_id
            )
            return
        
        target_health = target_entity.get_component(HealthComponent)
        if target_health is not None and target_health.current_health <= 0:
            self._target_lost = True
            self._log_projectile(
                "投射物目标丢失：目标已死亡",
                projectile_id=self.projectile_id,
                target_id=self.target_id
            )
            return
        
        target_transform = target_entity.get_component(TransformComponent)
        if target_transform is None:
            self._target_lost = True
            self._log_projectile(
                "投射物目标丢失：目标没有位置组件",
                projectile_id=self.projectile_id,
                target_id=self.target_id
            )
            return
        
        current_x = self.transform.x
        current_y = self.transform.y
        target_x = target_transform.x
        target_y = target_transform.y
        
        dx = target_x - current_x
        dy = target_y - current_y
        
        distance_squared = dx * dx + dy * dy
        hit_threshold = self.projectile_component.hit_threshold
        hit_threshold_squared = hit_threshold * hit_threshold
        
        if distance_squared < hit_threshold_squared:
            self._handle_hit(target_x, target_y)
            return
        
        distance = distance_squared ** 0.5
        max_move_distance = self.speed * delta
        
        if max_move_distance >= distance:
            self.transform.x = target_x
            self.transform.y = target_y
            self._handle_hit(target_x, target_y)
        else:
            ratio = max_move_distance / distance
            self.transform.x += dx * ratio
            self.transform.y += dy * ratio
    
    def _handle_hit(self, hit_x: float, hit_y: float) -> None:
        """
        处理击中目标。
        
        发布 ProjectileHitEvent 并标记投射物为非活动状态。
        
        参数：
            hit_x: 击中位置 X 坐标
            hit_y: 击中位置 Y 坐标
        """
        if self._has_hit:
            return
        
        self._has_hit = True
        
        if self.projectile_component is not None:
            self.projectile_component.is_active = False
        
        source_tower_id = (
            self.projectile_component.source_tower_id
            if self.projectile_component is not None
            else None
        )
        
        status_effects = (
            self.projectile_component.status_effects
            if self.projectile_component is not None
            else []
        )
        
        hit_event = ProjectileHitEvent(
            projectile_id=self.projectile_id,
            target_id=self.target_id,
            damage=self.projectile_component.damage if self.projectile_component else 0.0,
            hit_x=hit_x,
            hit_y=hit_y,
            source_tower_id=source_tower_id,
            status_effects=status_effects
        )
        
        publish(hit_event)
        
        self._log_projectile(
            "投射物击中目标",
            projectile_id=self.projectile_id,
            target_id=self.target_id,
            damage=self.projectile_component.damage if self.projectile_component else 0.0,
            position=(hit_x, hit_y)
        )
