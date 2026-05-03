"""
光源组件

LightSourceComponent 用于标记实体具有光源能力，可以驱散周围的黑雾。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯粹的数据容器，不包含任何业务逻辑。
所有光源相关的逻辑（如点亮/熄灭视野）都应该在 System 中实现。
============================================================================
"""

from dataclasses import dataclass


@dataclass
class LightSourceComponent:
    """
    光源组件，标记实体具有光源能力。
    
    属性：
        light_radius: 光源影响的半径（单位格数，使用曼哈顿距离计算）
        is_active: 光源是否激活（True 表示点亮，False 表示熄灭）
    
    使用示例：
        # 创建防御塔实体并添加光源组件
        entity = BaseEntity(entity_id=1)
        entity.add_component(TransformComponent(x=5.0, y=3.0))
        entity.add_component(LightSourceComponent(light_radius=2))
        
        # 光源半径为 2 意味着曼哈顿距离 <= 2 的格子都会被点亮
        # 例如：(5,3)、(4,3)、(5,2)、(6,3)、(5,4)、(3,3) 等
    """
    
    light_radius: int
    is_active: bool = True
