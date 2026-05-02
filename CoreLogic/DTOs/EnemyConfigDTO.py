"""
敌人配置数据传输对象

EnemyConfigDTO 定义敌人的配置数据结构，从外部 JSON 加载。

============================================================================
【架构规范强制声明】
============================================================================

此 DTO 是不可变的数据容器，仅用于数据传输。
业务逻辑（如敌人行为、战斗计算）应该在 EnemyManager 或战斗系统中实现。

============================================================================
"""

from dataclasses import dataclass
from typing import Any, Dict

from CoreLogic.DTOs.BaseConfigDTO import BaseConfigDTO


@dataclass(frozen=True)
class EnemyConfigDTO(BaseConfigDTO):
    """
    敌人配置数据传输对象。
    
    定义单个敌人类型的所有配置属性。
    
    属性：
        id: 敌人配置的唯一标识符
        name: 敌人的可读名称
        max_hp: 最大生命值
        speed: 移动速度（单位/秒）
        damage: 对玩家的伤害值
        reward: 击杀后获得的金币奖励
        description: 敌人的描述文本
        
    示例：
        enemy_config = EnemyConfigDTO(
            id="enemy_basic_001",
            name="基础影裔",
            max_hp=100,
            speed=1.5,
            damage=10,
            reward=10,
            description="最基础的敌人，移动缓慢但数量众多"
        )
    """
    max_hp: int
    speed: float
    damage: int
    reward: int
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnemyConfigDTO':
        """
        从字典创建 EnemyConfigDTO 实例。
        
        参数：
            data: 包含敌人配置的字典
            
        返回：
            EnemyConfigDTO 实例
        """
        return super().from_dict(data)
