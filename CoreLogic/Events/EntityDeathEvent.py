"""
实体死亡事件

EntityDeathEvent 用于在实体死亡时通知其他系统。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯粹的数据容器事件，用于跨域通信。
当实体死亡时，HealthSystem 会发布此事件，其他系统可以订阅并处理。

使用场景：
- 经济系统：给予击杀奖励
- UI系统：显示死亡特效或提示
- 任务系统：更新击杀计数
- 成就系统：检查成就条件
============================================================================
"""

from dataclasses import dataclass


@dataclass
class EntityDeathEvent:
    """
    实体死亡事件。
    
    当实体的生命值降至或低于 0 时，HealthSystem 会发布此事件。
    
    属性：
        entity_id: 死亡实体的 ID
        max_health: 实体的最大生命值（用于统计或成就）
    
    使用示例：
        # 订阅死亡事件
        from CoreLogic import subscribe, EntityDeathEvent
        
        def on_entity_death(event: EntityDeathEvent) -> None:
            print(f"实体 {event.entity_id} 已死亡")
        
        subscribe(EntityDeathEvent, on_entity_death)
        
        # 发布死亡事件（通常由 HealthSystem 自动发布）
        from CoreLogic import publish
        publish(EntityDeathEvent(entity_id=1, max_health=100))
    """
    
    entity_id: int
    max_health: float
