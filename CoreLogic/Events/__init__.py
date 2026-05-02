"""
游戏事件模块

包含所有领域事件的定义。

============================================================================
【架构规范强制声明】
============================================================================

不同域（如战斗系统、经济系统、UI系统、存档系统等）之间的交互，
必须通过投递 Event 进行，严禁跨域的强耦合直接调用。

正确示例：
    # 战斗系统发布事件
    publish(EntityDeathEvent(entity_id=1, max_health=100))
    
    # 其他系统订阅并处理
    subscribe(EntityDeathEvent, self._on_entity_death)

错误示例（严禁使用）：
    # 战斗系统直接调用其他系统方法（强耦合）
    self.reward_system.give_death_reward(entity_id)
============================================================================
"""

from CoreLogic.Events.EntityDeathEvent import EntityDeathEvent

__all__ = [
    'EntityDeathEvent',
]
