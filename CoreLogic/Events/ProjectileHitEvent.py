"""
投射物击中事件

ProjectileHitEvent 用于在投射物击中目标时通知其他系统。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯粹的数据容器事件，用于跨域通信。
当投射物击中目标敌人时，投射物系统会发布此事件，其他系统可以订阅并处理。

使用场景：
- 生命值系统：对目标造成伤害
- UI系统：显示击中特效
- 音效系统：播放击中音效
- 成就系统：检查成就条件
============================================================================
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProjectileHitEvent:
    """
    投射物击中事件。
    
    当投射物追踪到目标敌人并触发碰撞检测时，
    投射物系统会发布此事件通知其他系统。
    
    属性：
        projectile_id: 击中目标的投射物实体 ID
        target_id: 被击中的目标敌人实体 ID
        damage: 投射物携带的伤害值
        hit_x: 击中位置 X 坐标
        hit_y: 击中位置 Y 坐标
        source_tower_id: 发射此投射物的防御塔实体 ID（可选）
    
    使用示例：
        # 订阅击中事件
        from CoreLogic import subscribe, ProjectileHitEvent
        
        def on_projectile_hit(event: ProjectileHitEvent) -> None:
            print(f"投射物 {event.projectile_id} 击中了目标 {event.target_id}，造成 {event.damage} 点伤害")
        
        subscribe(ProjectileHitEvent, on_projectile_hit)
        
        # 发布击中事件（通常由投射物系统发布）
        from CoreLogic import publish
        publish(ProjectileHitEvent(
            projectile_id=10,
            target_id=5,
            damage=25.0,
            hit_x=6.0,
            hit_y=3.0,
            source_tower_id=1
        ))
    """
    
    projectile_id: int
    target_id: int
    damage: float
    hit_x: float
    hit_y: float
    source_tower_id: Optional[int] = None
