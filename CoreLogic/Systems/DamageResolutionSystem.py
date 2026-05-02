"""
伤害结算系统

DamageResolutionSystem 负责完成从投射物击中到敌人扣血的完整闭环。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯事件驱动的系统，监听 ProjectileHitEvent 并处理伤害结算。

关键设计决策（解耦性最强的方案）：
1. HomingMovementComponent 检测击中并发布 ProjectileHitEvent
2. DamageResolutionSystem 订阅 ProjectileHitEvent
3. DamageResolutionSystem 通过 ServiceLocator 获取 EntityManager
4. DamageResolutionSystem 验证目标敌人是否存活
5. 如果存活，调用 HealthSystem.take_damage() 进行扣血
6. HealthSystem 检测死亡并发布 EntityDeathEvent
7. DeathSystem 订阅 EntityDeathEvent 并销毁实体

这样的设计实现了最大程度的解耦：
- 投射物系统不需要知道生命值系统的存在
- 生命值系统不需要知道投射物系统的存在
- 死亡系统独立处理实体销毁

使用示例：
    # 初始化并启动伤害结算系统
    damage_resolution_system = DamageResolutionSystem()
    damage_resolution_system.initialize()  # 订阅 ProjectileHitEvent
    
    # 当投射物击中目标时，会自动：
    # 1. 验证敌人是否存活
    # 2. 对敌人造成伤害
    # 3. 输出战斗日志
    
    # 关闭时停止监听
    damage_resolution_system.shutdown()  # 取消订阅
============================================================================
"""

from typing import Optional

from CoreLogic.Core.EventBus import subscribe, unsubscribe
from CoreLogic.Core.ServiceLocator import try_get_service
from CoreLogic.Events.ProjectileHitEvent import ProjectileHitEvent
from CoreLogic.Managers.EntityManager import EntityManager
from CoreLogic.Systems.HealthSystem import HealthSystem
from CoreLogic.Components.HealthComponent import HealthComponent
from CoreLogic.Components.BuffComponent import BuffComponent
from CoreLogic.StatusEffects.StatusEffect import StatusEffect
from CoreLogic.Interfaces.IGameLogger import IGameLogger


class DamageResolutionSystem:
    """
    伤害结算系统。
    
    负责完成从投射物击中到敌人扣血的完整闭环：
    - 监听 ProjectileHitEvent
    - 验证目标敌人是否存活
    - 对存活的敌人造成伤害
    - 输出战斗日志
    
    特性：
    - 事件驱动：不每帧更新，仅在收到击中事件时工作
    - 完全解耦：通过 EventBus 和 ServiceLocator 与其他系统通信
    - 灵活可控：可随时调用 initialize() 和 shutdown() 来启停
    
    使用示例：
        damage_resolution_system = DamageResolutionSystem()
        damage_resolution_system.initialize()  # 开始监听击中事件
        
        # 此时任何投射物击中都会自动结算伤害
        
        damage_resolution_system.shutdown()  # 停止监听
    """
    
    def __init__(self) -> None:
        """
        初始化伤害结算系统。
        
        注意：这只是创建实例，需要手动调用 initialize() 开始监听事件。
        """
        self._is_initialized: bool = False
        self._health_system: HealthSystem = HealthSystem()
    
    def initialize(self) -> None:
        """
        初始化伤害结算系统，订阅 ProjectileHitEvent。
        
        调用此方法后，DamageResolutionSystem 开始监听投射物击中事件。
        当收到 ProjectileHitEvent 时，会：
        1. 从 ServiceLocator 获取 EntityManager
        2. 通过 target_id 获取目标敌人实体
        3. 检查敌人是否存活
        4. 如果存活，调用 HealthSystem.take_damage() 造成伤害
        5. 输出战斗日志
        
        注意：如果已经初始化过，此方法不做任何操作。
        """
        if self._is_initialized:
            return
        
        subscribe(ProjectileHitEvent, self._on_projectile_hit)
        self._is_initialized = True
    
    def shutdown(self) -> None:
        """
        关闭伤害结算系统，取消订阅 ProjectileHitEvent。
        
        调用此方法后，DamageResolutionSystem 不再监听击中事件。
        应该在系统关闭或不再需要伤害结算时调用。
        
        注意：如果未初始化，此方法不做任何操作。
        """
        if not self._is_initialized:
            return
        
        unsubscribe(ProjectileHitEvent, self._on_projectile_hit)
        self._is_initialized = False
    
    def is_initialized(self) -> bool:
        """
        检查伤害结算系统是否已初始化（正在监听事件）。
        
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
    
    def _log_combat(self, message: str, **kwargs) -> None:
        """
        记录战斗日志。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数
        """
        logger = self._get_logger()
        if logger is not None:
            logger.combat(message, **kwargs)
    
    def _format_hit_message(self, event: ProjectileHitEvent) -> str:
        """
        格式化击中日志消息。
        
        参数：
            event: ProjectileHitEvent 实例
            
        返回：
            格式化的日志消息字符串
        """
        tower_id = event.source_tower_id if event.source_tower_id is not None else "未知"
        return f"防御塔 {tower_id} 的投射物命中了敌人 {event.target_id}，造成了 {event.damage} 点伤害"
    
    def _on_projectile_hit(self, event: ProjectileHitEvent) -> None:
        """
        处理投射物击中事件。
        
        当收到 ProjectileHitEvent 时执行以下操作：
        1. 从 ServiceLocator 获取 EntityManager
        2. 通过 target_id 获取目标敌人实体
        3. 合法性校验：检查敌人是否仍然存活
           - 敌人实体是否存在
           - 敌人是否有 HealthComponent
           - 敌人的当前生命值是否 > 0
        4. 如果敌人存活：
           - 调用 HealthSystem.take_damage() 造成伤害
           - 输出战斗日志
        
        参数：
            event: ProjectileHitEvent 实例，包含击中信息
        """
        entity_manager = self._get_entity_manager()
        if entity_manager is None:
            return
        
        target_entity = entity_manager.get_entity(event.target_id)
        
        if target_entity is None:
            return
        
        if not self._health_system.is_alive(target_entity):
            return
        
        self._log_combat(
            self._format_hit_message(event),
            tower_id=event.source_tower_id,
            target_id=event.target_id,
            projectile_id=event.projectile_id,
            damage=event.damage,
            hit_position=(event.hit_x, event.hit_y)
        )
        
        self._health_system.take_damage(target_entity, event.damage)
        
        self._apply_status_effects(target_entity, event.status_effects)
    
    def _apply_status_effects(self, target_entity, status_effects: list[StatusEffect]) -> None:
        """
        应用状态效果到目标实体。
        
        如果目标实体没有 BuffComponent，则添加一个。
        然后将所有状态效果添加到 BuffComponent 中并应用。
        
        参数：
            target_entity: 目标实体
            status_effects: 要应用的状态效果列表
        """
        if not status_effects:
            return
        
        buff_comp = target_entity.get_component(BuffComponent)
        if buff_comp is None:
            buff_comp = BuffComponent()
            target_entity.add_component(buff_comp)
        
        for effect in status_effects:
            effect_copy = self._copy_effect(effect)
            buff_comp.add_effect(effect_copy)
            effect_copy.apply(target_entity)
            
            self._log_combat(
                "状态效果已应用",
                entity_id=target_entity.entity_id,
                effect_type=type(effect_copy).__name__,
                duration=effect_copy.duration,
            )
    
    def _copy_effect(self, effect: StatusEffect) -> StatusEffect:
        """
        创建状态效果的副本。
        
        由于状态效果包含时间状态，每个目标应该获得独立的副本。
        
        参数：
            effect: 原始状态效果
            
        返回：
            状态效果的新实例
        """
        return type(effect)(
            **{k: v for k, v in effect.__dict__.items() if not k.startswith('_')}
        )
