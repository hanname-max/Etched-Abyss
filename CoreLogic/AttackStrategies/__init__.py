"""
攻击策略模块

包含所有攻击策略的具体实现，使用策略模式实现可插拔的攻击行为。

============================================================================
【策略模式架构】
============================================================================

Context（上下文）: AttackComponent
- 持有当前 IAttackStrategy 实例的引用
- 提供 set_strategy 方法切换策略
- 攻击时委托给当前策略的 execute_fire 方法

Strategy（策略接口）: IAttackStrategy
- 定义 execute_fire 抽象方法
- 所有具体策略必须实现此接口

Concrete Strategies（具体策略）:
- SingleShotStrategy: 默认单发策略，只攻击锁定目标
- MultiShotStrategy: 多目标策略，攻击主目标及周围敌人

============================================================================
"""

from CoreLogic.AttackStrategies.SingleShotStrategy import SingleShotStrategy
from CoreLogic.AttackStrategies.MultiShotStrategy import MultiShotStrategy

__all__ = [
    'SingleShotStrategy',
    'MultiShotStrategy',
]
