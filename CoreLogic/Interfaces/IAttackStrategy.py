"""
攻击策略接口

IAttackStrategy 是策略模式的核心接口，定义防御塔的攻击行为。
不同的器官可以通过替换此接口的实现来改变防御塔的攻击机制。

============================================================================
【策略模式说明】
============================================================================

策略模式（Strategy Pattern）是一种行为设计模式，它定义了一系列算法，
并将每个算法封装起来，使它们可以相互替换。

在本系统中：
- IAttackStrategy: 抽象策略接口，定义 ExecuteFire 方法
- SingleShotStrategy: 具体策略，实现默认的单发攻击
- MultiShotStrategy: 具体策略，实现多目标分裂攻击
- AttackComponent: 上下文（Context），持有当前策略的引用

使用场景：
- 器官"分裂神经"装备时，切换到 MultiShotStrategy
- 器官卸下时，恢复默认的 SingleShotStrategy
============================================================================
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class IAttackStrategy(ABC):
    """
    攻击策略接口。
    
    所有攻击策略都必须实现此接口，定义 ExecuteFire 方法。
    防御塔的攻击行为由当前持有的策略决定。
    
    使用示例：
        # 创建策略实例
        single_shot = SingleShotStrategy()
        multi_shot = MultiShotStrategy(split_radius=2.0, max_additional_targets=2)
        
        # 切换防御塔的攻击策略
        attack_component.set_strategy(multi_shot)
        
        # 攻击时会自动使用当前策略
        attack_system.tick(delta)
    """
    
    @property
    @abstractmethod
    def strategy_id(self) -> str:
        """
        策略的唯一标识符。
        
        用于区分不同的策略类型，便于日志和调试。
        
        返回：
            策略标识符字符串，如 "single_shot" 或 "multi_shot"
        """
        pass
    
    @property
    @abstractmethod
    def projectile_speed(self) -> float:
        """
        获取投射物飞行速度。
        
        返回：
            投射物飞行速度（单位/秒）
        """
        pass
    
    @projectile_speed.setter
    @abstractmethod
    def projectile_speed(self, value: float) -> None:
        """
        设置投射物飞行速度。
        
        参数：
            value: 投射物飞行速度（单位/秒）
        """
        pass
    
    @abstractmethod
    def execute_fire(
        self,
        tower_entity: Any,
        primary_target_id: int,
        damage: float,
        status_effects: Optional[list] = None
    ) -> int:
        """
        执行攻击行为。
        
        此方法是策略模式的核心。不同的策略实现此方法来定义不同的攻击行为：
        - SingleShotStrategy: 只向主目标发射一个投射物
        - MultiShotStrategy: 向主目标和周围额外目标发射多个投射物
        
        参数：
            tower_entity: 防御塔实体（IEntity 实例），用于获取位置、组件等
            primary_target_id: 主目标的实体 ID（TargetingComponent 锁定的目标）
            damage: 基础伤害值（来自 TowerComponent.damage）
            status_effects: 可选的状态效果列表（如中毒、减速等）
            
        返回：
            发射的投射物数量（用于统计和调试）
        """
        pass
