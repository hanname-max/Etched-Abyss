"""
防御塔组件

TowerComponent 用于记录防御塔实体的基础属性。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯粹的数据容器，不包含任何业务逻辑。
所有防御塔相关的逻辑（如攻击、升级、卖出）都应该在 System 中实现。
============================================================================
"""

from dataclasses import dataclass
from typing import List


@dataclass
class TowerComponent:
    """
    防御塔组件，记录防御塔实体的基础属性。
    
    存储从 TowerConfigDTO 复制的配置属性，供战斗系统使用。
    
    属性：
        config_id: 防御塔配置的唯一标识符
        name: 防御塔的可读名称
        cost: 建造费用
        damage: 基础伤害值
        attack_range: 攻击范围（单位格数）
        attack_speed: 攻击速度（次/秒）
        description: 防御塔的描述文本
        upgrade_ids: 可升级到的后续防御塔 ID 列表
        
    使用示例：
        # 创建防御塔实体并添加组件
        entity = BaseEntity(entity_id=1)
        entity.add_component(TransformComponent(x=5.0, y=3.0))
        entity.add_component(TowerComponent(
            config_id="tower_arrow_001",
            name="箭塔",
            cost=100,
            damage=20,
            attack_range=3.0,
            attack_speed=1.0,
            description="基础远程防御塔",
            upgrade_ids=["tower_arrow_002"]
        ))
    """
    
    config_id: str
    name: str
    cost: int
    damage: int
    attack_range: float
    attack_speed: float
    description: str = ""
    upgrade_ids: List[str] = None
