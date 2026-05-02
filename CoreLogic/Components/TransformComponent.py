"""
变换组件

TransformComponent 用于记录实体在网格中的逻辑位置。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯粹的数据容器，不包含任何业务逻辑。
所有位置相关的逻辑（如移动、碰撞检测）都应该在 System 中实现。
============================================================================
"""

from dataclasses import dataclass


@dataclass
class TransformComponent:
    """
    变换组件，记录实体在网格中的逻辑位置。
    
    使用浮点数坐标以支持平滑移动和插值。
    
    属性：
        x: 网格中的 X 坐标（浮点数）
        y: 网格中的 Y 坐标（浮点数）
    
    使用示例：
        # 创建实体并添加变换组件
        entity = BaseEntity(entity_id=1)
        entity.add_component(TransformComponent(x=5.0, y=3.0))
        
        # 通过 System 处理移动逻辑
        class MovementSystem(ITickable):
            def tick(self, delta: float):
                for entity in world.query(TransformComponent, VelocityComponent):
                    transform = entity.get_component(TransformComponent)
                    velocity = entity.get_component(VelocityComponent)
                    transform.x += velocity.vx * delta
                    transform.y += velocity.vy * delta
    """
    
    x: float = 0.0
    y: float = 0.0
