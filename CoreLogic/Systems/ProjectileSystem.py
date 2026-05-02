"""
投射物系统

ProjectileSystem 负责管理投射物的生命周期：
1. 监听 TowerFiredEvent，创建投射物实体
2. 监听 ProjectileHitEvent，销毁已击中目标的投射物
3. 实现 ITickable 接口，每帧清理无效投射物

============================================================================
【架构规范强制声明】
============================================================================

这是一个事件驱动 + 每帧更新的混合系统：
- 事件驱动：监听 TowerFiredEvent 创建投射物，监听 ProjectileHitEvent 销毁投射物
- 每帧更新：实现 ITickable 接口，每帧清理已失效的投射物

关键设计决策（解耦性最强的方案）：
1. 战斗系统检测攻击时机并发布 TowerFiredEvent
2. ProjectileSystem 订阅 TowerFiredEvent
3. ProjectileSystem 通过 ServiceLocator 获取 EntityManager
4. ProjectileSystem 创建投射物实体并挂载必要组件
5. HomingMovementComponent 负责追踪移动和碰撞检测
6. 击中时 HomingMovementComponent 发布 ProjectileHitEvent
7. ProjectileSystem 订阅 ProjectileHitEvent 并销毁投射物

这样的设计实现了最大程度的解耦：
- 战斗系统不需要知道投射物系统的存在
- 投射物系统通过事件和服务定位器与其他系统通信
- 其他系统（UI系统、音效系统）也可以独立订阅相关事件
============================================================================
"""

from typing import Optional

from CoreLogic import (
    subscribe,
    unsubscribe,
    TowerFiredEvent,
    ProjectileHitEvent,
    EntityManager,
    TransformComponent,
    ProjectileComponent,
    HomingMovementComponent,
    ITickable,
    try_get_service,
)
from CoreLogic.Interfaces.IGameLogger import IGameLogger


class ProjectileSystem(ITickable):
    """
    投射物系统。
    
    负责管理投射物的完整生命周期：
    - 监听 TowerFiredEvent 并创建投射物实体
    - 监听 ProjectileHitEvent 并销毁已击中的投射物
    - 每帧清理已失效的投射物（目标丢失、飞出范围等）
    
    特性：
    - 事件驱动：通过订阅事件来创建和销毁投射物
    - 服务定位：通过 ServiceLocator 获取 EntityManager
    - 每帧更新：实现 ITickable 接口，注册到 GameLoopManager 获得每帧更新
    
    使用示例：
        # 初始化并启动投射物系统
        projectile_system = ProjectileSystem()
        projectile_system.initialize()  # 订阅事件
        
        # 注册到 GameLoopManager 以获得每帧更新
        from CoreLogic import GameLoopManager, get_service
        loop_manager = get_service(GameLoopManager)
        loop_manager.register_tickable(projectile_system)
        
        # 此时发布 TowerFiredEvent 会自动创建投射物
        # 投射物击中目标后会自动发布 ProjectileHitEvent 并被销毁
        
        # 关闭时停止监听
        projectile_system.shutdown()  # 取消订阅
    """
    
    HIT_THRESHOLD: float = 0.1
    
    def __init__(self) -> None:
        """
        初始化投射物系统。
        
        注意：这只是创建实例，需要手动调用 initialize() 开始监听事件，
        并注册到 GameLoopManager 以获得每帧更新。
        """
        self._is_initialized: bool = False
    
    def initialize(self) -> None:
        """
        初始化投射物系统，订阅相关事件。
        
        调用此方法后，ProjectileSystem 开始监听：
        - TowerFiredEvent：防御塔发射事件，触发时创建投射物
        - ProjectileHitEvent：投射物击中事件，触发时销毁投射物
        
        注意：如果已经初始化过，此方法不做任何操作。
        """
        if self._is_initialized:
            return
        
        subscribe(TowerFiredEvent, self._on_tower_fired)
        subscribe(ProjectileHitEvent, self._on_projectile_hit)
        self._is_initialized = True
    
    def shutdown(self) -> None:
        """
        关闭投射物系统，取消订阅事件。
        
        调用此方法后，ProjectileSystem 不再监听事件。
        应该在系统关闭或不再需要投射物处理时调用。
        
        注意：如果未初始化，此方法不做任何操作。
        """
        if not self._is_initialized:
            return
        
        unsubscribe(TowerFiredEvent, self._on_tower_fired)
        unsubscribe(ProjectileHitEvent, self._on_projectile_hit)
        self._is_initialized = False
    
    def is_initialized(self) -> bool:
        """
        检查投射物系统是否已初始化（正在监听事件）。
        
        返回：
            True 如果已初始化并正在监听；否则返回 False
        """
        return self._is_initialized
    
    def _get_entity_manager(self) -> Optional[EntityManager]:
        """
        从 ServiceLocator 获取 EntityManager。
        
        返回：
            EntityManager 实例，如果未注册则返回 None
        """
        return try_get_service(EntityManager)
    
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
    
    def _on_tower_fired(self, event: TowerFiredEvent) -> None:
        """
        处理防御塔发射事件。
        
        当收到 TowerFiredEvent 时：
        1. 从 ServiceLocator 获取 EntityManager
        2. 创建新的投射物实体
        3. 挂载必要的组件：
           - TransformComponent: 记录发射起始位置
           - ProjectileComponent: 记录伤害值、目标ID、击中阈值
           - HomingMovementComponent: 负责追踪移动和碰撞检测
        4. 记录日志
        
        参数：
            event: TowerFiredEvent 实例，包含发射信息
        """
        entity_manager = self._get_entity_manager()
        if entity_manager is None:
            return
        
        projectile_entity = entity_manager.create_entity()
        projectile_id = projectile_entity.entity_id
        
        transform = TransformComponent(x=event.start_x, y=event.start_y)
        projectile_entity.add_component(transform)
        
        projectile_component = ProjectileComponent(
            damage=event.damage,
            target_id=event.target_id,
            source_tower_id=event.tower_id,
            hit_threshold=self.HIT_THRESHOLD
        )
        projectile_entity.add_component(projectile_component)
        
        homing_component = HomingMovementComponent(
            speed=event.speed,
            target_id=event.target_id,
            projectile_id=projectile_id,
            transform=transform,
            projectile_component=projectile_component
        )
        projectile_entity.add_component(homing_component)
        
        self._log_projectile(
            "投射物已创建",
            projectile_id=projectile_id,
            tower_id=event.tower_id,
            target_id=event.target_id,
            damage=event.damage,
            speed=event.speed,
            start_position=(event.start_x, event.start_y)
        )
    
    def _on_projectile_hit(self, event: ProjectileHitEvent) -> None:
        """
        处理投射物击中事件。
        
        当收到 ProjectileHitEvent 时：
        1. 从 ServiceLocator 获取 EntityManager
        2. 调用 destroy_entity 销毁投射物实体
        
        参数：
            event: ProjectileHitEvent 实例，包含击中信息
        """
        entity_manager = self._get_entity_manager()
        if entity_manager is None:
            return
        
        entity_manager.destroy_entity(event.projectile_id)
        
        self._log_projectile(
            "投射物已销毁（击中目标）",
            projectile_id=event.projectile_id,
            target_id=event.target_id,
            damage=event.damage,
            hit_position=(event.hit_x, event.hit_y)
        )
    
    def tick(self, delta: float) -> None:
        """
        每帧更新方法，实现 ITickable 接口。
        
        由 GameLoopManager 每帧调用。
        
        更新逻辑：
        1. 从 ServiceLocator 获取 EntityManager
        2. 查询所有拥有 ProjectileComponent 的实体
        3. 对每个投射物检查是否需要销毁：
           - ProjectileComponent.is_active == False（已击中目标）
           - HomingMovementComponent.is_active == False（目标丢失）
        4. 销毁所有需要清理的投射物
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
        """
        if delta < 0:
            delta = 0.0
        
        entity_manager = self._get_entity_manager()
        if entity_manager is None:
            return
        
        projectile_entities = entity_manager.get_entities_with_component(ProjectileComponent)
        
        entities_to_destroy: list[int] = []
        
        for entity in projectile_entities:
            projectile_comp = entity.get_component(ProjectileComponent)
            homing_comp = entity.get_component(HomingMovementComponent)
            
            if projectile_comp is None:
                continue
            
            should_destroy = False
            
            if not projectile_comp.is_active:
                should_destroy = True
            
            if homing_comp is not None and not homing_comp.is_active:
                should_destroy = True
            
            if should_destroy:
                entities_to_destroy.append(entity.entity_id)
        
        for entity_id in entities_to_destroy:
            entity_manager.destroy_entity(entity_id)
            
            self._log_projectile(
                "投射物已销毁（清理无效投射物）",
                projectile_id=entity_id
            )
    
    def get_active_projectile_count(self) -> int:
        """
        获取当前活动投射物的数量。
        
        返回：
            拥有 ProjectileComponent 且 is_active == True 的实体数量
        """
        entity_manager = self._get_entity_manager()
        if entity_manager is None:
            return 0
        
        count = 0
        projectile_entities = entity_manager.get_entities_with_component(ProjectileComponent)
        
        for entity in projectile_entities:
            projectile_comp = entity.get_component(ProjectileComponent)
            if projectile_comp is not None and projectile_comp.is_active:
                count += 1
        
        return count
