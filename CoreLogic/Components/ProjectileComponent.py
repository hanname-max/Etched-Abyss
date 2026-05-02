"""
投射物组件

ProjectileComponent 用于记录投射物实体的基础属性。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯粹的数据容器，不包含任何业务逻辑。
所有投射物相关的逻辑（如追踪移动、碰撞检测）都应该在 System 中实现。
============================================================================
"""

from dataclasses import dataclass, field
from typing import Optional, List

from CoreLogic.StatusEffects.StatusEffect import StatusEffect


@dataclass
class ProjectileComponent:
    """
    投射物组件，记录投射物实体的基础属性。
    
    存储投射物的核心属性，供投射物系统使用。
    
    属性：
        damage: 投射物携带的伤害值
        target_id: 目标敌人实体 ID（用于追踪）
        source_tower_id: 发射此投射物的防御塔 ID（用于统计或成就）
        is_active: 投射物是否处于活动状态
        hit_threshold: 击中判定的距离阈值（单位：格）
        status_effects: 投射物携带的状态效果列表（如中毒、减速等）
    
    使用示例：
        # 创建投射物实体并添加组件
        entity = BaseEntity(entity_id=10)
        entity.add_component(TransformComponent(x=5.0, y=3.0))
        entity.add_component(ProjectileComponent(
            damage=25.0,
            target_id=5,
            source_tower_id=1,
            hit_threshold=0.1,
            status_effects=[PoisonEffect(duration=5.0, damage_percent=0.05)]
        ))
    """
    
    damage: float
    target_id: int
    source_tower_id: Optional[int] = None
    is_active: bool = True
    hit_threshold: float = 0.1
    status_effects: List[StatusEffect] = field(default_factory=list)
