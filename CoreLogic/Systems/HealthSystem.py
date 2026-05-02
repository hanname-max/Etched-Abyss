"""
生命值系统

HealthSystem 负责处理所有与生命值相关的业务逻辑。

============================================================================
【架构规范强制声明】
============================================================================

HealthSystem 是业务逻辑的实现者，负责：
- 扣血和回血逻辑
- 死亡检测
- 战斗日志记录
- 死亡事件发布

HealthComponent 只是纯粹的数据容器，不包含任何业务逻辑。
============================================================================
"""

from typing import Optional, Callable
from dataclasses import dataclass

from CoreLogic import (
    IEntity,
    get_service,
    try_get_service,
    IGameLogger,
    publish,
)
from CoreLogic.Components.HealthComponent import HealthComponent
from CoreLogic.Events.EntityDeathEvent import EntityDeathEvent


@dataclass
class DeathContext:
    """
    死亡上下文。
    
    用于传递给 OnDeath 回调的上下文信息。
    
    属性：
        entity_id: 死亡实体的 ID
        current_health: 死亡时的当前生命值
        max_health: 最大生命值
        damage_dealt: 造成死亡的伤害值
    """
    
    entity_id: int
    current_health: float
    max_health: float
    damage_dealt: float


OnDeathCallback = Callable[[DeathContext], None]


class HealthSystem:
    """
    生命值系统。
    
    负责处理所有与生命值相关的业务逻辑：
    - 扣血（take_damage）
    - 回血（heal）
    - 死亡检测
    - 战斗日志记录
    - 死亡事件发布
    - 死亡回调管理
    
    使用示例：
        # 创建实体
        entity = BaseEntity(entity_id=1)
        entity.add_component(HealthComponent(current_health=100, max_health=100))
        
        # 创建生命值系统
        health_system = HealthSystem()
        
        # 注册死亡回调
        def on_death(context: DeathContext) -> None:
            print(f"实体 {context.entity_id} 已死亡！")
        
        health_system.register_on_death(entity.entity_id, on_death)
        
        # 扣血
        health_system.take_damage(entity, 30)  # 剩余 70
        health_system.take_damage(entity, 80)  # 剩余 -10，触发死亡
        
        # 或者订阅全局死亡事件
        from CoreLogic import subscribe, EntityDeathEvent
        subscribe(EntityDeathEvent, handle_global_death)
    """
    
    def __init__(self) -> None:
        """
        初始化生命值系统。
        """
        self._on_death_callbacks: dict[int, list[OnDeathCallback]] = {}
    
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
    
    def register_on_death(self, entity_id: int, callback: OnDeathCallback) -> None:
        """
        注册实体死亡回调。
        
        当指定实体死亡时，所有已注册的回调将被调用。
        
        参数：
            entity_id: 实体 ID
            callback: 回调函数，签名为 def callback(context: DeathContext) -> None
        
        使用示例：
            def on_death(context: DeathContext) -> None:
                print(f"实体 {context.entity_id} 已死亡！")
            
            health_system.register_on_death(entity.entity_id, on_death)
        """
        if entity_id not in self._on_death_callbacks:
            self._on_death_callbacks[entity_id] = []
        self._on_death_callbacks[entity_id].append(callback)
    
    def unregister_on_death(self, entity_id: int, callback: OnDeathCallback) -> None:
        """
        注销实体死亡回调。
        
        参数：
            entity_id: 实体 ID
            callback: 要注销的回调函数
        """
        if entity_id in self._on_death_callbacks:
            try:
                self._on_death_callbacks[entity_id].remove(callback)
            except ValueError:
                pass
    
    def clear_on_death(self, entity_id: int) -> None:
        """
        清除指定实体的所有死亡回调。
        
        参数：
            entity_id: 实体 ID
        """
        if entity_id in self._on_death_callbacks:
            del self._on_death_callbacks[entity_id]
    
    def take_damage(self, entity: IEntity, amount: float) -> float:
        """
        对实体造成伤害。
        
        扣除实体的当前生命值，并在扣血前后记录战斗日志。
        如果生命值降至或低于 0，将触发死亡事件和死亡回调。
        
        参数：
            entity: 目标实体（必须包含 HealthComponent）
            amount: 伤害值（非负值，负值将被视为 0）
        
        返回：
            扣除后的当前生命值
        
        日志输出：
            - 扣血前：记录伤害来源和剩余血量
            - 扣血后：记录新的剩余血量
            - 死亡时：记录死亡事件
        
        触发事件：
            - EntityDeathEvent: 当生命值 <= 0 时发布
        
        使用示例：
            # 对实体造成 25 点伤害
            remaining = health_system.take_damage(entity, 25)
            print(f"剩余生命值: {remaining}")
        """
        health = entity.get_component(HealthComponent)
        if health is None:
            return 0.0
        
        amount = max(0.0, amount)
        if amount <= 0.0:
            return health.current_health
        
        entity_id = entity.entity_id
        old_health = health.current_health
        
        self._log_combat(
            "实体受到伤害",
            entity_id=entity_id,
            damage=amount,
            current_health=old_health,
            max_health=health.max_health,
        )
        
        health.current_health -= amount
        new_health = health.current_health
        
        self._log_combat(
            "生命值已更新",
            entity_id=entity_id,
            old_health=old_health,
            new_health=new_health,
            max_health=health.max_health,
        )
        
        if new_health <= 0.0 and old_health > 0.0:
            self._handle_death(entity, health, amount)
        
        return new_health
    
    def heal(self, entity: IEntity, amount: float) -> float:
        """
        恢复实体的生命值。
        
        增加实体的当前生命值，但不会超过最大生命值。
        
        参数：
            entity: 目标实体（必须包含 HealthComponent）
            amount: 恢复值（非负值，负值将被视为 0）
        
        返回：
            恢复后的当前生命值
        
        使用示例：
            # 恢复 30 点生命值
            remaining = health_system.heal(entity, 30)
            print(f"剩余生命值: {remaining}")
        """
        health = entity.get_component(HealthComponent)
        if health is None:
            return 0.0
        
        amount = max(0.0, amount)
        if amount <= 0.0:
            return health.current_health
        
        entity_id = entity.entity_id
        old_health = health.current_health
        
        self._log_combat(
            "实体恢复生命值",
            entity_id=entity_id,
            heal_amount=amount,
            current_health=old_health,
            max_health=health.max_health,
        )
        
        health.current_health = min(
            health.current_health + amount,
            health.max_health
        )
        new_health = health.current_health
        
        self._log_combat(
            "生命值已更新",
            entity_id=entity_id,
            old_health=old_health,
            new_health=new_health,
            max_health=health.max_health,
        )
        
        return new_health
    
    def is_alive(self, entity: IEntity) -> bool:
        """
        检查实体是否存活。
        
        参数：
            entity: 目标实体
        
        返回：
            如果实体有 HealthComponent 且 current_health > 0，返回 True；
            否则返回 False
        """
        health = entity.get_component(HealthComponent)
        if health is None:
            return False
        return health.current_health > 0.0
    
    def get_health_percentage(self, entity: IEntity) -> float:
        """
        获取实体的生命值百分比。
        
        参数：
            entity: 目标实体
        
        返回：
            生命值百分比（0.0 - 1.0），如果没有 HealthComponent 或 max_health 为 0，返回 0.0
        """
        health = entity.get_component(HealthComponent)
        if health is None or health.max_health <= 0.0:
            return 0.0
        return max(0.0, health.current_health) / health.max_health
    
    def _handle_death(
        self,
        entity: IEntity,
        health: HealthComponent,
        damage_dealt: float,
    ) -> None:
        """
        处理实体死亡。
        
        记录死亡日志，发布死亡事件，并调用已注册的死亡回调。
        
        参数：
            entity: 死亡实体
            health: HealthComponent 实例
            damage_dealt: 造成死亡的伤害值
        """
        entity_id = entity.entity_id
        
        self._log_combat(
            "实体已死亡",
            entity_id=entity_id,
            final_health=health.current_health,
            max_health=health.max_health,
            damage_dealt=damage_dealt,
        )
        
        publish(EntityDeathEvent(
            entity_id=entity_id,
            max_health=health.max_health,
        ))
        
        if entity_id in self._on_death_callbacks:
            context = DeathContext(
                entity_id=entity_id,
                current_health=health.current_health,
                max_health=health.max_health,
                damage_dealt=damage_dealt,
            )
            for callback in self._on_death_callbacks[entity_id]:
                callback(context)
