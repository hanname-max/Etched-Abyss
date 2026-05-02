"""
数据传输对象（DTO）模块

包含所有配置数据的 DTO 定义，用于从外部 JSON 文件加载数据。

============================================================================
【架构规范强制声明】
============================================================================

所有 DTO 都是不可变的数据容器，仅用于数据传输，不应包含业务逻辑。
业务逻辑应该在对应的 Manager 或 Service 中实现。

DTO 命名规范：
- 以 ConfigDTO 结尾（如 EnemyConfigDTO, TowerConfigDTO）
- 从 BaseConfigDTO 继承

============================================================================
"""

from CoreLogic.DTOs.BaseConfigDTO import BaseConfigDTO
from CoreLogic.DTOs.EnemyConfigDTO import EnemyConfigDTO
from CoreLogic.DTOs.TowerConfigDTO import TowerConfigDTO
from CoreLogic.DTOs.WaveConfigDTO import WaveConfigDTO, EnemySpawnConfig
from CoreLogic.DTOs.OrganConfigDTO import OrganConfigDTO

__all__ = [
    'BaseConfigDTO',
    'EnemyConfigDTO',
    'TowerConfigDTO',
    'WaveConfigDTO',
    'EnemySpawnConfig',
    'OrganConfigDTO',
]
