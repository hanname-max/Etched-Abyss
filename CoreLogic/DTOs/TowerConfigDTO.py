"""
防御塔配置数据传输对象

TowerConfigDTO 定义防御塔的配置数据结构，从外部 JSON 加载。

============================================================================
【架构规范强制声明】
============================================================================

此 DTO 是不可变的数据容器，仅用于数据传输。
业务逻辑（如攻击计算、升级逻辑）应该在 TowerManager 或战斗系统中实现。

============================================================================
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from CoreLogic.DTOs.BaseConfigDTO import BaseConfigDTO


@dataclass(frozen=True)
class TowerConfigDTO(BaseConfigDTO):
    """
    防御塔配置数据传输对象。
    
    定义单个防御塔类型的所有配置属性。
    
    属性：
        id: 防御塔配置的唯一标识符
        name: 防御塔的可读名称
        cost: 建造费用
        damage: 基础伤害值
        attack_range: 攻击范围（单位格数）
        attack_speed: 攻击速度（次/秒）
        max_health: 最大生命值（用于攻城模式下敌人攻击防御塔）
        description: 防御塔的描述文本
        upgrade_ids: 可升级到的后续防御塔 ID 列表
        
    示例：
        tower_config = TowerConfigDTO(
            id="tower_arrow_001",
            name="箭塔",
            cost=100,
            damage=20,
            attack_range=3,
            attack_speed=1.0,
            max_health=100,
            description="基础远程防御塔，攻击速度适中",
            upgrade_ids=["tower_arrow_002", "tower_cannon_001"]
        )
    """
    cost: int
    damage: int
    attack_range: float
    attack_speed: float
    max_health: float = 100.0
    light_radius: int = 0
    description: str = ""
    upgrade_ids: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TowerConfigDTO':
        """
        从字典创建 TowerConfigDTO 实例。
        
        参数：
            data: 包含防御塔配置的字典
            
        返回：
            TowerConfigDTO 实例
        """
        return super().from_dict(data)
