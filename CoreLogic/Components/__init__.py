"""
游戏组件模块

包含所有游戏逻辑组件的定义。

============================================================================
【架构规范强制声明】
============================================================================

所有 Component 都是纯粹的数据容器，不包含任何业务逻辑。
所有业务逻辑都应该在 System 中实现，通过查询拥有特定 Component
组合的 Entity 来处理。

例外：MovementComponent
MovementComponent 实现了 IUpdateable 接口，用于自驱动的路径移动。
它在 update 中会直接修改关联的 TransformComponent。
这是一个有意识的设计选择，用于简化路径移动逻辑。
============================================================================
"""

from CoreLogic.Components.TransformComponent import TransformComponent
from CoreLogic.Components.HealthComponent import HealthComponent
from CoreLogic.Components.MovementComponent import MovementComponent

__all__ = [
    'TransformComponent',
    'HealthComponent',
    'MovementComponent',
]
