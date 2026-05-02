"""
中毒效果实现

PoisonEffect 实现了中毒状态效果：
- 每隔一秒对敌人造成基于最大生命值百分比的真实伤害
- 直接调用 TakeDamage
- 持续时间结束后自动移除

============================================================================
【架构规范说明】
============================================================================

PoisonEffect 继承自 StatusEffect，实现了：
1. 周期性伤害：每隔 1 秒造成一次伤害
2. 真实伤害：基于目标最大生命值的百分比伤害
3. 伤害计算：damage = max_health * damage_percent

使用方式：
    # 创建中毒效果（持续5秒，每秒造成5%最大生命值伤害）
    poison = PoisonEffect(duration=5.0, damage_percent=0.05)
    
    # 应用到敌人
    poison.on_apply(enemy_entity)
    
    # 每帧更新
    poison.tick(delta, enemy_entity)
    
    # 效果过期后自动移除
    if poison.is_expired:
        poison.on_remove(enemy_entity)
============================================================================
"""

from typing import Optional

from CoreLogic.StatusEffects.StatusEffect import StatusEffect
from CoreLogic.Components.HealthComponent import HealthComponent
from CoreLogic.Interfaces.IGameLogger import IGameLogger
from CoreLogic.Core.ServiceLocator import try_get_service


class PoisonEffect(StatusEffect):
    """
    中毒效果。
    
    每隔 1 秒对目标造成基于最大生命值百分比的真实伤害。
    
    属性：
        duration: 总持续时间（秒）
        damage_percent: 每秒造成的伤害占最大生命值的百分比（0.0 - 1.0）
        tick_interval: 伤害触发间隔（默认 1.0 秒）
        remaining_time: 剩余持续时间
        _time_since_last_tick: 距离上次伤害的时间
        _health_system: 生命值系统实例
        
    使用示例：
        # 创建中毒效果：持续5秒，每秒造成5%最大生命值伤害
        poison = PoisonEffect(duration=5.0, damage_percent=0.05)
        
        # 应用到敌人
        poison.on_apply(enemy)
        
        # 每帧更新（会自动每隔1秒造成伤害）
        poison.tick(delta, enemy)
    """
    
    def __init__(
        self,
        duration: float,
        damage_percent: float,
        tick_interval: float = 1.0,
    ) -> None:
        """
        初始化中毒效果。
        
        参数：
            duration: 总持续时间（秒）
            damage_percent: 每秒造成的伤害占最大生命值的百分比（0.0 - 1.0）
                例如：0.05 表示每秒造成 5% 最大生命值的伤害
            tick_interval: 伤害触发间隔（秒），默认 1.0 秒
        """
        super().__init__(duration)
        
        self.damage_percent: float = max(0.0, min(1.0, damage_percent))
        self.tick_interval: float = max(0.0, tick_interval)
        self._time_since_last_tick: float = 0.0
        self._health_system = None
    
    def _get_health_system(self):
        """
        延迟获取 HealthSystem 实例。
        
        使用延迟导入来避免循环依赖问题。
        """
        if self._health_system is None:
            from CoreLogic.Systems.HealthSystem import HealthSystem
            self._health_system = HealthSystem()
        return self._health_system
    
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
    
    def on_apply(self, target) -> None:
        """
        中毒效果首次应用时的回调。
        
        记录中毒开始的日志。
        
        参数：
            target: 目标实体
        """
        entity_id = target.entity_id
        
        self._log_combat(
            "目标中毒",
            entity_id=entity_id,
            duration=self.duration,
            damage_percent=self.damage_percent,
        )
    
    def on_remove(self, target) -> None:
        """
        中毒效果移除时的回调。
        
        记录中毒结束的日志。
        
        参数：
            target: 目标实体
        """
        entity_id = target.entity_id
        
        self._log_combat(
            "目标中毒效果结束",
            entity_id=entity_id,
        )
    
    def on_tick(self, delta: float, target) -> None:
        """
        每帧更新的回调。
        
        累计时间，当达到 tick_interval 时造成伤害。
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
            target: 目标实体
        """
        if self.is_expired:
            return
        
        self._time_since_last_tick += delta
        
        while self._time_since_last_tick >= self.tick_interval:
            self._time_since_last_tick -= self.tick_interval
            self._deal_poison_damage(target)
    
    def _deal_poison_damage(self, target) -> None:
        """
        造成中毒伤害。
        
        伤害值 = 目标最大生命值 * damage_percent
        直接调用 HealthSystem.take_damage 造成真实伤害。
        
        参数：
            target: 目标实体
        """
        health = target.get_component(HealthComponent)
        if health is None:
            return
        
        damage = health.max_health * self.damage_percent
        
        self._log_combat(
            "中毒伤害",
            entity_id=target.entity_id,
            damage=damage,
            max_health=health.max_health,
            damage_percent=self.damage_percent,
            current_health=health.current_health,
        )
        
        self._get_health_system().take_damage(target, damage)
    
    def reset_tick_timer(self) -> None:
        """
        重置伤害计时器。
        
        用于效果叠加时重置计时。
        """
        self._time_since_last_tick = 0.0
