"""
高疯狂值事件

OnHighInsanityEvent 用于在全局疯狂值超过阈值时通知其他系统。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯粹的数据容器事件，用于跨域通信。
当 InsanityManager 检测到疯狂值超过 80 时，会发布此事件，
其他系统（如 TargetingComponent）可以订阅并处理。

使用场景：
- TargetingComponent：索敌距离减半或攻击力获得 1.5 倍伤害乘区
- UI系统：显示视觉疯狂效果
- 成就系统：检查疯狂相关成就
============================================================================
"""

from dataclasses import dataclass


@dataclass
class OnHighInsanityEvent:
    """
    高疯狂值事件。
    
    当全局疯狂值超过阈值（默认 80）时发布，
    或当疯狂值从高值回落至阈值以下时发布。
    
    属性：
        current_insanity: 当前疯狂值（0~100）
        is_high_insanity: 是否处于高疯狂状态（True=超过阈值，False=回落至阈值以下）
        threshold: 触发此事件的阈值（默认 80）
    
    使用示例：
        # 订阅高疯狂值事件
        from CoreLogic import subscribe, OnHighInsanityEvent
        
        def on_high_insanity(event: OnHighInsanityEvent) -> None:
            if event.is_high_insanity:
                print(f"疯狂值已达到 {event.current_insanity}，进入高疯狂状态！")
            else:
                print(f"疯狂值已回落至 {event.current_insanity}，高疯狂状态解除。")
        
        subscribe(OnHighInsanityEvent, on_high_insanity)
        
        # 发布高疯狂值事件（通常由 InsanityManager 自动发布）
        from CoreLogic import publish
        publish(OnHighInsanityEvent(current_insanity=85.0, is_high_insanity=True, threshold=80))
    """
    
    current_insanity: float
    is_high_insanity: bool
    threshold: float = 80.0
