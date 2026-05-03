"""
器官配置数据传输对象

OrganConfigDTO 定义器官的配置数据结构，从外部 JSON 加载。

============================================================================
【架构规范强制声明】
============================================================================

此 DTO 是不可变的数据容器，仅用于数据传输。
业务逻辑（如器官融合、属性计算）应该在 Manager 或 System 中实现。

============================================================================
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from CoreLogic.DTOs.BaseConfigDTO import BaseConfigDTO


@dataclass(frozen=True)
class OrganConfigDTO(BaseConfigDTO):
    """
    器官配置数据传输对象。
    
    定义单个器官类型的所有配置属性。
    器官是防御塔的可插拔组件，通过融合来增强防御塔的属性。
    
    属性：
        id: 器官配置的唯一标识符（OrganId）
        name: 器官的可读名称
        description: 器官的描述文本
        attribute_modifiers: 属性修饰器参数列表，每个参数包含属性名和修饰值
        insanity_gain: 装备此器官时增加的疯狂值（默认 0），极端器官如"古神视神经"会有较高值
        
    示例：
        # 普通器官
        organ_config = OrganConfigDTO(
            id="organ_heart_001",
            name="强化之心",
            description="增加防御塔攻击力 20%",
            attribute_modifiers=[
                {"attribute": "damage", "value": 0.2, "type": "percentage"},
                {"attribute": "attack_speed", "value": 0.1, "type": "percentage"}
            ]
        )
        
        # 极端器官（增加疯狂值）
        ancient_eye = OrganConfigDTO(
            id="organ_ancient_eye_001",
            name="古神视神经",
            description="来自深渊的凝视：攻击范围大幅增加，但会提高疯狂值",
            attribute_modifiers=[
                {"attribute": "attack_range", "value": 2.0, "type": "additive"}
            ],
            insanity_gain=25.0
        )
    """
    description: str = ""
    attribute_modifiers: List[Dict[str, Any]] = field(default_factory=list)
    insanity_gain: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrganConfigDTO':
        """
        从字典创建 OrganConfigDTO 实例。
        
        参数：
            data: 包含器官配置的字典
            
        返回：
            OrganConfigDTO 实例
        """
        return super().from_dict(data)
