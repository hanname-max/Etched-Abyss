"""
关卡波次配置数据传输对象

WaveConfigDTO 定义关卡波次的配置数据结构，从外部 JSON 加载。

============================================================================
【架构规范强制声明】
============================================================================

此 DTO 是不可变的数据容器，仅用于数据传输。
业务逻辑（如波次生成、敌人调度）应该在 WaveManager 或关卡系统中实现。

============================================================================
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from CoreLogic.DTOs.BaseConfigDTO import BaseConfigDTO


@dataclass(frozen=True)
class EnemySpawnConfig:
    """
    单个敌人生成配置。
    
    用于定义波次中每一波的敌人配置。
    
    属性：
        enemy_id: 敌人配置的 ID
        count: 生成数量
        spawn_interval: 生成间隔（秒）
        delay_before: 在这组敌人之前的延迟（秒）
    """
    enemy_id: str
    count: int
    spawn_interval: float = 1.0
    delay_before: float = 0.0


@dataclass(frozen=True)
class WaveConfigDTO(BaseConfigDTO):
    """
    关卡波次配置数据传输对象。
    
    定义单个波次的所有配置属性。
    
    属性：
        id: 波次配置的唯一标识符
        name: 波次的可读名称
        level_id: 所属关卡的 ID
        wave_number: 波次序号
        enemy_spawns: 敌人生成配置列表
        reward: 完成此波次的奖励
        description: 波次的描述文本
        
    示例：
        wave_config = WaveConfigDTO(
            id="wave_01_001",
            name="第一关 第一波",
            level_id="level_001",
            wave_number=1,
            enemy_spawns=[
                EnemySpawnConfig(enemy_id="enemy_basic_001", count=5, spawn_interval=1.5),
                EnemySpawnConfig(enemy_id="enemy_basic_001", count=3, spawn_interval=1.0, delay_before=2.0)
            ],
            reward=50,
            description="基础影裔的小规模入侵"
        )
    """
    level_id: str
    wave_number: int
    enemy_spawns: List[EnemySpawnConfig]
    reward: int
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WaveConfigDTO':
        """
        从字典创建 WaveConfigDTO 实例。
        
        特殊处理 enemy_spawns 列表，将其转换为 EnemySpawnConfig 对象。
        
        参数：
            data: 包含波次配置的字典
            
        返回：
            WaveConfigDTO 实例
        """
        if 'enemy_spawns' in data and isinstance(data['enemy_spawns'], list):
            spawn_list = []
            for spawn_data in data['enemy_spawns']:
                if isinstance(spawn_data, dict):
                    spawn_list.append(EnemySpawnConfig(**spawn_data))
                else:
                    spawn_list.append(spawn_data)
            data = data.copy()
            data['enemy_spawns'] = spawn_list
        
        return super().from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        """
        将 DTO 转换为字典。
        
        特殊处理 enemy_spawns 列表，将 EnemySpawnConfig 对象转换为字典。
        
        返回：
            包含所有字段的字典
        """
        result = super().to_dict()
        if 'enemy_spawns' in result and isinstance(result['enemy_spawns'], list):
            result['enemy_spawns'] = [
                {
                    'enemy_id': s.enemy_id,
                    'count': s.count,
                    'spawn_interval': s.spawn_interval,
                    'delay_before': s.delay_before
                }
                for s in result['enemy_spawns']
            ]
        return result
