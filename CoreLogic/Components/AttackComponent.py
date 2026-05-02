"""
攻击组件

AttackComponent 是策略模式中的 Context（上下文），
负责持有攻击策略引用和管理攻击冷却状态。

============================================================================
【策略模式架构】
============================================================================

Context: AttackComponent
- 持有 IAttackStrategy 实例的引用
- 提供 set_strategy 方法切换攻击策略
- 管理攻击冷却计时器

Strategy: IAttackStrategy
- 定义 execute_fire 抽象方法

Concrete Strategies:
- SingleShotStrategy: 默认单发策略
- MultiShotStrategy: 多目标分裂策略

============================================================================
【架构规范说明】
============================================================================

此组件是架构规范的例外（类似于 TargetingComponent），
它专注于状态管理（策略引用、冷却计时），实际的业务逻辑
（冷却更新、攻击触发）由 AttackSystem 处理。

这确保了：
- 组件仍然主要是数据容器
- 复杂的业务逻辑在 System 中实现
- 策略模式的实现清晰且易于维护
============================================================================
"""

from dataclasses import dataclass, field
from typing import Optional

from CoreLogic.Interfaces.IAttackStrategy import IAttackStrategy
from CoreLogic.AttackStrategies.SingleShotStrategy import SingleShotStrategy


@dataclass
class AttackComponent:
    """
    攻击组件，策略模式的上下文（Context）。
    
    负责持有攻击策略引用和管理攻击冷却状态。
    与 AttackSystem 配合使用，实现防御塔的攻击行为。
    
    属性：
        current_strategy: 当前使用的攻击策略，默认是 SingleShotStrategy
        cooldown_remaining: 剩余冷却时间（秒）
        _default_strategy: 缓存的默认策略，用于恢复默认行为
        
    使用示例：
        # 创建攻击组件
        attack = AttackComponent()
        
        # 切换到多发策略（装备分裂神经器官时）
        from CoreLogic.AttackStrategies import MultiShotStrategy
        multi_shot = MultiShotStrategy(split_radius=2.0, max_additional_targets=2)
        attack.set_strategy(multi_shot)
        
        # 恢复默认策略（卸下分裂神经器官时）
        attack.reset_to_default()
        
        # 获取当前策略 ID
        print(attack.strategy_id)  # 输出 "single_shot" 或 "multi_shot"
    """
    
    current_strategy: IAttackStrategy = field(default_factory=SingleShotStrategy)
    cooldown_remaining: float = 0.0
    _default_strategy: Optional[IAttackStrategy] = field(default=None, repr=False)
    
    def __post_init__(self) -> None:
        """
        初始化后处理。
        
        确保 _default_strategy 被正确设置，
        以便 reset_to_default 可以恢复默认策略。
        """
        if self._default_strategy is None:
            if isinstance(self.current_strategy, SingleShotStrategy):
                self._default_strategy = self.current_strategy
            else:
                self._default_strategy = SingleShotStrategy()
    
    @property
    def strategy_id(self) -> str:
        """
        获取当前策略的标识符。
        
        便捷属性，用于快速判断当前使用的策略类型。
        
        返回：
            当前策略的 strategy_id，如 "single_shot" 或 "multi_shot"
        """
        return self.current_strategy.strategy_id
    
    @property
    def is_ready(self) -> bool:
        """
        检查攻击是否准备就绪（冷却已完成）。
        
        返回：
            True 如果 cooldown_remaining <= 0，否则 False
        """
        return self.cooldown_remaining <= 0.0
    
    def set_strategy(self, strategy: IAttackStrategy) -> None:
        """
        设置新的攻击策略。
        
        由器官系统调用，当装备特殊攻击器官时切换策略。
        
        参数：
            strategy: 新的攻击策略实例（必须实现 IAttackStrategy 接口）
            
        示例：
            # 装备分裂神经器官时
            multi_shot = MultiShotStrategy(split_radius=2.0, max_additional_targets=2)
            attack_component.set_strategy(multi_shot)
        """
        if strategy is None:
            return
        
        self.current_strategy = strategy
    
    def reset_to_default(self) -> None:
        """
        恢复到默认攻击策略。
        
        由器官系统调用，当卸下特殊攻击器官时恢复默认行为。
        默认策略是 SingleShotStrategy。
        """
        if self._default_strategy is not None:
            self.current_strategy = self._default_strategy
        else:
            self.current_strategy = SingleShotStrategy()
            self._default_strategy = self.current_strategy
    
    def update_cooldown(self, delta: float) -> None:
        """
        更新冷却时间。
        
        由 AttackSystem 每帧调用，减少剩余冷却时间。
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
        """
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= delta
            if self.cooldown_remaining < 0:
                self.cooldown_remaining = 0.0
    
    def start_cooldown(self, cooldown_duration: float) -> None:
        """
        开始新的冷却周期。
        
        攻击完成后调用，设置下一次攻击的冷却时间。
        
        参数：
            cooldown_duration: 冷却持续时间（秒），通常来自 TowerComponent.attack_cooldown
        """
        if cooldown_duration > 0:
            self.cooldown_remaining = cooldown_duration
    
    def execute_attack(
        self,
        tower_entity,
        target_id: int,
        damage: float,
        status_effects=None
    ) -> int:
        """
        执行攻击（委托给当前策略）。
        
        这是策略模式的核心委托调用。
        AttackComponent 本身不实现攻击逻辑，
        而是将攻击行为委托给当前持有的 IAttackStrategy 实例。
        
        参数：
            tower_entity: 防御塔实体
            target_id: 主目标 ID
            damage: 伤害值
            status_effects: 可选的状态效果列表
            
        返回：
            发射的投射物数量（由策略的 execute_fire 返回）
        """
        if self.current_strategy is None:
            return 0
        
        return self.current_strategy.execute_fire(
            tower_entity=tower_entity,
            primary_target_id=target_id,
            damage=damage,
            status_effects=status_effects
        )
