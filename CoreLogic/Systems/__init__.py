"""
游戏系统模块

包含所有游戏逻辑系统的定义。

============================================================================
【架构规范强制声明】
============================================================================

System 负责实现业务逻辑，通过查询拥有特定 Component 组合的 Entity 来处理。
Component 是纯粹的数据容器，不包含任何业务逻辑。

正确示例：
    class HealthSystem(ITickable):
        def tick(self, delta: float):
            for entity in world.query(HealthComponent):
                health = entity.get_component(HealthComponent)
                # 处理生命值相关逻辑

错误示例（严禁使用）：
    class HealthComponent:
        def take_damage(self, amount):  # 业务逻辑不应该在 Component 中
            self.current -= amount
============================================================================
"""

from CoreLogic.Systems.HealthSystem import HealthSystem
from CoreLogic.Systems.DeathSystem import DeathSystem
from CoreLogic.Systems.ProjectileSystem import ProjectileSystem
from CoreLogic.Systems.DamageResolutionSystem import DamageResolutionSystem
from CoreLogic.Systems.BuffSystem import BuffSystem
from CoreLogic.Systems.AttackSystem import AttackSystem
from CoreLogic.Systems.DynamicRepathingSystem import DynamicRepathingSystem
from CoreLogic.Systems.SiegeSystem import SiegeSystem

__all__ = [
    'HealthSystem',
    'DeathSystem',
    'ProjectileSystem',
    'DamageResolutionSystem',
    'BuffSystem',
    'AttackSystem',
    'DynamicRepathingSystem',
    'SiegeSystem',
]
