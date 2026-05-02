"""
防御塔发射事件

TowerFiredEvent 用于在防御塔发射攻击时通知其他系统。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯粹的数据容器事件，用于跨域通信。
当防御塔准备发射攻击时，战斗系统会发布此事件，其他系统可以订阅并处理。

使用场景：
- 投射物系统：创建投射物实体
- UI系统：显示发射特效
- 音效系统：播放发射音效
============================================================================
"""

from dataclasses import dataclass


@dataclass
class TowerFiredEvent:
    """
    防御塔发射事件。
    
    当防御塔锁定目标并准备发射攻击时，战斗系统会发布此事件。
    投射物系统订阅此事件来创建飞行的投射物实体。
    
    属性：
        tower_id: 发射攻击的防御塔实体 ID
        target_id: 目标敌人实体 ID
        damage: 投射物携带的伤害值
        start_x: 发射起始位置 X 坐标
        start_y: 发射起始位置 Y 坐标
        speed: 投射物飞行速度（单位/秒）
    
    使用示例：
        # 订阅发射事件
        from CoreLogic import subscribe, TowerFiredEvent
        
        def on_tower_fired(event: TowerFiredEvent) -> None:
            print(f"塔 {event.tower_id} 发射了攻击，目标: {event.target_id}")
        
        subscribe(TowerFiredEvent, on_tower_fired)
        
        # 发布发射事件（通常由战斗系统发布）
        from CoreLogic import publish
        publish(TowerFiredEvent(
            tower_id=1,
            target_id=5,
            damage=25,
            start_x=5.0,
            start_y=3.0,
            speed=8.0
        ))
    """
    
    tower_id: int
    target_id: int
    damage: float
    start_x: float
    start_y: float
    speed: float
