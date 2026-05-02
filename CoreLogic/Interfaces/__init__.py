"""
接口定义模块

包含所有核心接口定义，用于模块间解耦。

============================================================================
【架构规范强制声明】
============================================================================

不同域（如战斗系统、经济系统、UI系统、存档系统等）之间的交互，
必须通过投递 Event 进行，严禁跨域的强耦合直接调用。

正确示例：
    战斗系统 -> 发布 EnemyKilledEvent -> 经济系统订阅并处理奖励
    而不是：战斗系统直接调用 economic_system.add_gold()

违反此规范的代码将被视为架构缺陷，需要重构。
============================================================================
"""

from CoreLogic.Interfaces.IEvent import IEvent
from CoreLogic.Interfaces.IDataLoader import IDataLoader
from CoreLogic.Interfaces.IGameLogger import IGameLogger
from CoreLogic.Interfaces.ITickable import ITickable
from CoreLogic.Interfaces.IComponent import IComponent
from CoreLogic.Interfaces.IEntity import IEntity
from CoreLogic.Interfaces.IUpdateable import IUpdateable

__all__ = [
    'IEvent',
    'IDataLoader',
    'IGameLogger',
    'ITickable',
    'IComponent',
    'IEntity',
    'IUpdateable',
]
