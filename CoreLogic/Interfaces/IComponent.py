"""
游戏组件接口定义

IComponent 是所有游戏组件的基类空接口。

============================================================================
【架构规范强制声明】
============================================================================

在 ECS 架构中，Component 是纯粹的数据容器，不包含任何业务逻辑。
所有逻辑都应该在 System 中实现，通过查询拥有特定 Component 组合的 Entity 来处理。

正确示例：
    @dataclass
    class PositionComponent:
        x: float
        y: float
    
    class MovementSystem(ITickable):
        def tick(self, delta: float):
            # 查询同时拥有 Position 和 Velocity 组件的实体
            for entity in world.query(PositionComponent, VelocityComponent):
                pos = entity.get_component(PositionComponent)
                vel = entity.get_component(VelocityComponent)
                pos.x += vel.x * delta
                pos.y += vel.y * delta

错误示例（严禁使用）：
    # Component 中包含逻辑
    class PositionComponent:
        def __init__(self, x, y):
            self.x = x
            self.y = y
        
        def move(self, dx, dy):  # 这是逻辑，不应该在 Component 中
            self.x += dx
            self.y += dy
============================================================================
"""

from typing import Protocol


class IComponent(Protocol):
    """
    游戏组件基接口。
    
    所有游戏组件都应该实现（或被视为实现）此协议接口。
    这是一个空的标记接口，用于类型安全的组件操作。
    
    Component 是纯粹的数据容器，不包含任何业务逻辑。
    所有逻辑都应该在 System 中实现。
    
    使用示例：
        @dataclass
        class HealthComponent:
            current: int
            max: int
        
        该类自动满足 IComponent 协议，无需显式继承。
    """
    pass
