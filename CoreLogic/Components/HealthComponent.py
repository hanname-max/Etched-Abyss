"""
生命值组件

HealthComponent 用于记录实体的生命值数据。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯粹的数据容器，不包含任何业务逻辑。
所有生命值相关的逻辑（如扣血、死亡检测、回血）都应该在 System 中实现。

使用 HealthSystem 来处理：
- take_damage(amount): 扣除血量
- heal(amount): 恢复血量
- 死亡检测和事件触发
- 战斗日志记录
============================================================================
"""

from dataclasses import dataclass


@dataclass
class HealthComponent:
    """
    生命值组件，记录实体的当前生命值和最大生命值。
    
    属性：
        current_health: 当前生命值
        max_health: 最大生命值
    
    使用示例：
        # 创建实体并添加生命值组件
        entity = BaseEntity(entity_id=1)
        entity.add_component(HealthComponent(current_health=100, max_health=100))
        
        # 通过 HealthSystem 处理扣血逻辑
        health_system = HealthSystem()
        health_system.take_damage(entity, 25)  # 扣除 25 点伤害
        
        # 订阅死亡事件
        subscribe(EntityDeathEvent, on_entity_death)
    """
    
    current_health: float
    max_health: float
