"""
状态效果模块

包含所有状态效果（Status Effect）的定义和实现。

============================================================================
【架构规范说明】
============================================================================

StatusEffect 是状态效果的基类，包含：
- 持续时间和剩余时间管理
- 每帧更新逻辑
- 应用和移除效果的回调

与 Component 的区别：
- Component：纯粹的数据容器，不包含业务逻辑
- StatusEffect：包含数据和逻辑，用于实现持续的效果（如中毒、减速等）

使用方式：
1. 创建 StatusEffect 实例（如 PoisonEffect）
2. 将其添加到目标实体的 BuffComponent 中
3. BuffSystem 会在每帧调用所有 StatusEffect 的 update 方法
============================================================================
"""

from CoreLogic.StatusEffects.StatusEffect import StatusEffect
from CoreLogic.StatusEffects.PoisonEffect import PoisonEffect

__all__ = [
    'StatusEffect',
    'PoisonEffect',
]
