"""
模拟数据加载器实现

MockDataLoader 是 IDataLoader 接口的 Mock 实现，
内部硬编码返回模拟的 DTO 数据，用于纯逻辑单元测试，
不需要实际的 JSON 文件或 I/O 操作。

============================================================================
【使用场景】
============================================================================

1. 单元测试：在不需要真实数据文件的情况下测试业务逻辑
2. 开发前期：在数据文件结构尚未确定时进行快速原型开发
3. 边界情况测试：可以轻松构造各种边界数据进行测试

============================================================================
"""

from typing import Dict, List, Optional

from CoreLogic.Interfaces.IDataLoader import IDataLoader
from CoreLogic.DTOs import (
    EnemyConfigDTO,
    TowerConfigDTO,
    WaveConfigDTO,
    EnemySpawnConfig,
)


class MockDataLoader(IDataLoader):
    """
    模拟数据加载器。
    
    硬编码返回预设的模拟数据，用于单元测试。
    不涉及任何文件 I/O 操作。
    
    示例：
        # 创建 Mock 数据加载器
        mock_loader = MockDataLoader()
        
        # 注册到 ServiceLocator
        register_service(IDataLoader, mock_loader)
        
        # 后续代码可以通过接口获取数据
        enemy = get_service(IDataLoader).load_enemy_config("enemy_basic_001")
    """

    def __init__(self):
        """初始化 Mock 数据加载器，预加载模拟数据。"""
        self._enemy_configs: Dict[str, EnemyConfigDTO] = self._create_mock_enemies()
        self._tower_configs: Dict[str, TowerConfigDTO] = self._create_mock_towers()
        self._wave_configs: Dict[str, WaveConfigDTO] = self._create_mock_waves()

    def _create_mock_enemies(self) -> Dict[str, EnemyConfigDTO]:
        """创建模拟的敌人配置数据。"""
        return {
            "enemy_basic_001": EnemyConfigDTO(
                id="enemy_basic_001",
                name="基础影裔",
                max_hp=100,
                speed=1.5,
                damage=10,
                reward=10,
                description="最基础的敌人，移动缓慢但数量众多。它们是深渊的先锋军。"
            ),
            "enemy_fast_001": EnemyConfigDTO(
                id="enemy_fast_001",
                name="疾影者",
                max_hp=60,
                speed=3.0,
                damage=8,
                reward=15,
                description="速度极快的敌人，生命值较低但难以拦截。"
            ),
            "enemy_tank_001": EnemyConfigDTO(
                id="enemy_tank_001",
                name="重甲影卫",
                max_hp=300,
                speed=0.8,
                damage=25,
                reward=30,
                description="生命值极高的敌人，移动缓慢但破坏力巨大。"
            ),
        }

    def _create_mock_towers(self) -> Dict[str, TowerConfigDTO]:
        """创建模拟的防御塔配置数据。"""
        return {
            "tower_arrow_001": TowerConfigDTO(
                id="tower_arrow_001",
                name="箭塔",
                cost=100,
                damage=20,
                attack_range=3.0,
                attack_speed=1.0,
                description="基础远程防御塔，攻击速度适中，适合应对各种敌人。",
                upgrade_ids=["tower_arrow_002", "tower_cannon_001"]
            ),
            "tower_cannon_001": TowerConfigDTO(
                id="tower_cannon_001",
                name="炮塔",
                cost=200,
                damage=50,
                attack_range=2.5,
                attack_speed=0.5,
                description="高伤害但攻击速度慢的防御塔，适合对付重甲敌人。",
                upgrade_ids=["tower_cannon_002"]
            ),
            "tower_ice_001": TowerConfigDTO(
                id="tower_ice_001",
                name="冰霜塔",
                cost=150,
                damage=10,
                attack_range=2.5,
                attack_speed=1.2,
                description="攻击会减速敌人的特殊防御塔，控制效果极佳。",
                upgrade_ids=["tower_ice_002"]
            ),
        }

    def _create_mock_waves(self) -> Dict[str, WaveConfigDTO]:
        """创建模拟的波次配置数据。"""
        return {
            "wave_01_001": WaveConfigDTO(
                id="wave_01_001",
                name="第一关 第一波",
                level_id="level_001",
                wave_number=1,
                enemy_spawns=[
                    EnemySpawnConfig(
                        enemy_id="enemy_basic_001",
                        count=5,
                        spawn_interval=1.5,
                        delay_before=0.0
                    )
                ],
                reward=50,
                description="基础影裔的小规模入侵。这是玩家面临的第一波敌人。"
            ),
            "wave_01_002": WaveConfigDTO(
                id="wave_01_002",
                name="第一关 第二波",
                level_id="level_001",
                wave_number=2,
                enemy_spawns=[
                    EnemySpawnConfig(
                        enemy_id="enemy_basic_001",
                        count=8,
                        spawn_interval=1.2,
                        delay_before=0.0
                    ),
                    EnemySpawnConfig(
                        enemy_id="enemy_fast_001",
                        count=3,
                        spawn_interval=1.0,
                        delay_before=5.0
                    )
                ],
                reward=80,
                description="混合敌人编队，疾影者会在后期出现，需要注意防御。"
            ),
            "wave_01_003": WaveConfigDTO(
                id="wave_01_003",
                name="第一关 第三波",
                level_id="level_001",
                wave_number=3,
                enemy_spawns=[
                    EnemySpawnConfig(
                        enemy_id="enemy_basic_001",
                        count=6,
                        spawn_interval=1.0,
                        delay_before=0.0
                    ),
                    EnemySpawnConfig(
                        enemy_id="enemy_tank_001",
                        count=2,
                        spawn_interval=3.0,
                        delay_before=3.0
                    )
                ],
                reward=120,
                description="重甲影卫首次出现！需要高伤害的防御塔才能有效应对。"
            ),
        }

    def load_enemy_config(self, enemy_id: str) -> Optional[EnemyConfigDTO]:
        """
        加载指定 ID 的敌人配置。
        
        参数：
            enemy_id: 敌人配置的唯一标识符
            
        返回：
            EnemyConfigDTO 实例，如果不存在则返回 None
        """
        return self._enemy_configs.get(enemy_id)

    def load_tower_config(self, tower_id: str) -> Optional[TowerConfigDTO]:
        """
        加载指定 ID 的防御塔配置。
        
        参数：
            tower_id: 防御塔配置的唯一标识符
            
        返回：
            TowerConfigDTO 实例，如果不存在则返回 None
        """
        return self._tower_configs.get(tower_id)

    def load_wave_config(self, wave_id: str) -> Optional[WaveConfigDTO]:
        """
        加载指定 ID 的波次配置。
        
        参数：
            wave_id: 波次配置的唯一标识符
            
        返回：
            WaveConfigDTO 实例，如果不存在则返回 None
        """
        return self._wave_configs.get(wave_id)

    def load_all_enemy_configs(self) -> List[EnemyConfigDTO]:
        """
        加载所有敌人配置。
        
        返回：
            所有 EnemyConfigDTO 实例的列表
        """
        return list(self._enemy_configs.values())

    def load_all_tower_configs(self) -> List[TowerConfigDTO]:
        """
        加载所有防御塔配置。
        
        返回：
            所有 TowerConfigDTO 实例的列表
        """
        return list(self._tower_configs.values())

    def load_all_wave_configs(self) -> List[WaveConfigDTO]:
        """
        加载所有波次配置。
        
        返回：
            所有 WaveConfigDTO 实例的列表
        """
        return list(self._wave_configs.values())

    def load_wave_configs_by_level(self, level_id: str) -> List[WaveConfigDTO]:
        """
        加载指定关卡的所有波次配置。
        
        参数：
            level_id: 关卡的唯一标识符
            
        返回：
            该关卡所有 WaveConfigDTO 实例的列表，按波次序号排序
        """
        waves = [
            wave for wave in self._wave_configs.values()
            if wave.level_id == level_id
        ]
        waves.sort(key=lambda w: w.wave_number)
        return waves
