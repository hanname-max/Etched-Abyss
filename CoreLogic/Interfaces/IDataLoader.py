"""
数据加载器接口定义

IDataLoader 是所有配置数据加载器的基接口。
用于从外部数据源（如 JSON 文件）加载配置数据。

============================================================================
【架构规范强制声明】
============================================================================

所有数据加载器都应该实现此接口。
业务逻辑不应该直接依赖具体的加载器实现，而应该依赖此接口。

正确示例：
    # 依赖抽象接口
    def __init__(self, data_loader: IDataLoader):
        self._data_loader = data_loader
    
    # 使用接口方法
    enemy_config = self._data_loader.load_enemy_config("enemy_001")

错误示例（严禁使用）：
    # 直接依赖具体实现
    def __init__(self):
        self._data_loader = JsonDataLoader("data/")  # 强耦合

违反此规范的代码将被视为架构缺陷，需要重构。
============================================================================
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from CoreLogic.DTOs import (
    EnemyConfigDTO,
    TowerConfigDTO,
    WaveConfigDTO,
)


class IDataLoader(ABC):
    """
    数据加载器基接口。
    
    定义了从外部数据源加载配置数据的统一接口。
    所有具体的加载器实现（如 JsonDataLoader、MockDataLoader）都应该实现此接口。
    
    使用示例：
        # 通过 ServiceLocator 获取数据加载器
        data_loader = get_service(IDataLoader)
        
        # 加载单个配置
        enemy = data_loader.load_enemy_config("enemy_basic_001")
        tower = data_loader.load_tower_config("tower_arrow_001")
        
        # 加载所有配置
        all_enemies = data_loader.load_all_enemy_configs()
    """

    @abstractmethod
    def load_enemy_config(self, enemy_id: str) -> Optional[EnemyConfigDTO]:
        """
        加载指定 ID 的敌人配置。
        
        参数：
            enemy_id: 敌人配置的唯一标识符
            
        返回：
            EnemyConfigDTO 实例，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def load_tower_config(self, tower_id: str) -> Optional[TowerConfigDTO]:
        """
        加载指定 ID 的防御塔配置。
        
        参数：
            tower_id: 防御塔配置的唯一标识符
            
        返回：
            TowerConfigDTO 实例，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def load_wave_config(self, wave_id: str) -> Optional[WaveConfigDTO]:
        """
        加载指定 ID 的波次配置。
        
        参数：
            wave_id: 波次配置的唯一标识符
            
        返回：
            WaveConfigDTO 实例，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def load_all_enemy_configs(self) -> List[EnemyConfigDTO]:
        """
        加载所有敌人配置。
        
        返回：
            所有 EnemyConfigDTO 实例的列表
        """
        pass

    @abstractmethod
    def load_all_tower_configs(self) -> List[TowerConfigDTO]:
        """
        加载所有防御塔配置。
        
        返回：
            所有 TowerConfigDTO 实例的列表
        """
        pass

    @abstractmethod
    def load_all_wave_configs(self) -> List[WaveConfigDTO]:
        """
        加载所有波次配置。
        
        返回：
            所有 WaveConfigDTO 实例的列表
        """
        pass

    @abstractmethod
    def load_wave_configs_by_level(self, level_id: str) -> List[WaveConfigDTO]:
        """
        加载指定关卡的所有波次配置。
        
        参数：
            level_id: 关卡的唯一标识符
            
        返回：
            该关卡所有 WaveConfigDTO 实例的列表，按波次序号排序
        """
        pass
