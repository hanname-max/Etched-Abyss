"""
攻击系统

AttackSystem 负责管理防御塔的攻击冷却和触发攻击行为。

============================================================================
【策略模式集成】
============================================================================

AttackSystem 与策略模式的协作：
1. 每帧更新所有防御塔的攻击冷却（AttackComponent.cooldown_remaining）
2. 当冷却完成且 TargetingComponent 锁定目标时，触发攻击
3. 攻击行为委托给 AttackComponent.current_strategy.execute_fire
4. 不同的策略实现不同的攻击逻辑（单发 vs 多发）

============================================================================
【架构规范强制声明】
============================================================================

这是一个 System，负责实现业务逻辑：
- 查询拥有特定 Component 组合的 Entity
- 处理冷却更新和攻击触发
- 通过委托给 Strategy 实现攻击行为

Component 只是数据容器：
- TowerComponent: 提供攻击冷却时长
- TargetingComponent: 提供锁定的目标
- AttackComponent: 持有策略引用和当前冷却状态
============================================================================
"""

from typing import Optional

from CoreLogic.Interfaces.ITickable import ITickable
from CoreLogic.Components.TowerComponent import TowerComponent
from CoreLogic.Components.TargetingComponent import TargetingComponent
from CoreLogic.Components.AttackComponent import AttackComponent
from CoreLogic.Managers.InsanityManager import InsanityManager
from CoreLogic.Core.ServiceLocator import try_get_service
from CoreLogic.Managers.EntityManager import EntityManager
from CoreLogic.Interfaces.IGameLogger import IGameLogger


class AttackSystem(ITickable):
    """
    攻击系统。
    
    负责管理防御塔的攻击冷却和触发攻击行为。
    与 AttackComponent 和 IAttackStrategy 协作，实现策略模式的攻击机制。
    
    核心职责：
    1. 每帧更新所有防御塔的攻击冷却
    2. 检查冷却是否完成且有锁定目标
    3. 触发攻击（委托给当前策略）
    4. 攻击完成后重置冷却
    
    使用示例：
        # 初始化攻击系统
        attack_system = AttackSystem()
        attack_system.initialize()
        
        # 注册到 GameLoopManager 以获得每帧更新
        from CoreLogic import GameLoopManager, get_service
        loop_manager = get_service(GameLoopManager)
        loop_manager.register_tickable(attack_system)
        
        # 此时防御塔会自动：
        # - 每帧更新冷却
        # - 冷却完成且有目标时自动攻击
        # - 攻击后重置冷却
        
        # 关闭时停止
        attack_system.shutdown()
    """
    
    def __init__(self) -> None:
        """
        初始化攻击系统。
        
        注意：这只是创建实例，需要手动调用 initialize()，
        并注册到 GameLoopManager 以获得每帧更新。
        """
        self._is_initialized: bool = False
    
    def initialize(self) -> None:
        """
        初始化攻击系统。
        
        目前没有需要订阅的事件，但保留此方法以保持与其他系统的一致性。
        未来可能需要监听器官装备/卸下事件来切换策略。
        """
        if self._is_initialized:
            return
        
        self._is_initialized = True
    
    def shutdown(self) -> None:
        """
        关闭攻击系统。
        """
        if not self._is_initialized:
            return
        
        self._is_initialized = False
    
    def is_initialized(self) -> bool:
        """
        检查攻击系统是否已初始化。
        
        返回：
            True 如果已初始化；否则返回 False
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
    
    def _get_insanity_manager(self) -> Optional[InsanityManager]:
        """
        从 ServiceLocator 获取疯狂值管理器。
        
        返回：
            如果已注册，返回 InsanityManager 实例；否则返回 None
        """
        return try_get_service(InsanityManager)
    
    def _get_effective_damage(self, base_damage: float) -> float:
        """
        获取当前有效的伤害值。
        
        在高疯狂状态下，攻击力获得 1.5 倍伤害乘区（高风险高回报机制）。
        
        参数：
            base_damage: 基础伤害值
            
        返回：
            应用乘区后的有效伤害值
        """
        insanity_manager = self._get_insanity_manager()
        if insanity_manager is not None and insanity_manager.is_high_insanity():
            multiplier = insanity_manager.high_insanity_damage_multiplier
            return base_damage * multiplier
        
        return base_damage
    
    def _log_attack(self, message: str, **kwargs) -> None:
        """
        记录攻击相关日志。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数
        """
        logger = self._get_logger()
        if logger is not None:
            logger.info(message, **kwargs)
    
    def tick(self, delta: float) -> None:
        """
        每帧更新方法，实现 ITickable 接口。
        
        由 GameLoopManager 每帧调用。
        
        更新逻辑：
        1. 从 ServiceLocator 获取 EntityManager
        2. 查询所有拥有 TowerComponent + TargetingComponent + AttackComponent 的实体
        3. 对每个防御塔：
           a. 更新攻击冷却
           b. 检查冷却是否完成且有锁定目标
           c. 如果准备就绪，执行攻击
           d. 攻击完成后重置冷却
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
        """
        if delta < 0:
            delta = 0.0
        
        entity_manager = self._get_entity_manager()
        if entity_manager is None:
            return
        
        entities = entity_manager.get_entities_with_component(TowerComponent)
        
        for entity in entities:
            tower_comp = entity.get_component(TowerComponent)
            targeting_comp = entity.get_component(TargetingComponent)
            attack_comp = entity.get_component(AttackComponent)
            
            if tower_comp is None:
                continue
            
            if attack_comp is None:
                continue
            
            attack_comp.update_cooldown(delta)
            
            if targeting_comp is None:
                continue
            
            if not attack_comp.is_ready:
                continue
            
            if not targeting_comp.has_target:
                continue
            
            target_id = targeting_comp.current_target_id
            if target_id is None:
                continue
            
            base_damage = tower_comp.damage
            damage = self._get_effective_damage(base_damage)
            
            insanity_manager = self._get_insanity_manager()
            is_high_insanity = insanity_manager is not None and insanity_manager.is_high_insanity()
            
            projectile_count = attack_comp.execute_attack(
                tower_entity=entity,
                target_id=target_id,
                damage=damage,
                status_effects=None
            )
            
            cooldown_duration = tower_comp.attack_cooldown
            attack_comp.start_cooldown(cooldown_duration)
            
            log_kwargs = {
                "tower_id": entity.entity_id,
                "target_id": target_id,
                "damage": damage,
                "base_damage": base_damage,
                "projectile_count": projectile_count,
                "strategy_id": attack_comp.strategy_id,
                "next_cooldown": cooldown_duration,
                "high_insanity": is_high_insanity
            }
            
            if is_high_insanity and insanity_manager is not None:
                log_kwargs["damage_multiplier"] = insanity_manager.high_insanity_damage_multiplier
            
            self._log_attack(
                "防御塔已攻击",
                **log_kwargs
            )
