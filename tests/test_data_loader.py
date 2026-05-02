import pytest
from dataclasses import FrozenInstanceError
from typing import Optional

from CoreLogic import (
    BaseConfigDTO,
    EnemyConfigDTO,
    TowerConfigDTO,
    WaveConfigDTO,
    EnemySpawnConfig,
    IDataLoader,
    MockDataLoader,
    ServiceLocator,
    register_service,
    get_service,
)


class TestBaseConfigDTO:
    """测试配置数据传输对象基类"""

    def test_from_dict_creates_instance(self):
        """测试从字典创建 DTO 实例"""
        data = {
            "id": "test_001",
            "name": "测试配置",
            "max_hp": 100,
            "speed": 1.5,
            "damage": 10,
            "reward": 5,
            "extra_field": "应该被忽略"
        }
        
        enemy = EnemyConfigDTO.from_dict(data)
        
        assert enemy.id == "test_001"
        assert enemy.name == "测试配置"
        assert enemy.max_hp == 100
        assert enemy.speed == 1.5
        assert enemy.damage == 10
        assert enemy.reward == 5

    def test_to_dict_converts_back(self):
        """测试 DTO 转换回字典"""
        enemy = EnemyConfigDTO(
            id="enemy_001",
            name="测试敌人",
            max_hp=100,
            speed=1.5,
            damage=10,
            reward=5
        )
        
        data = enemy.to_dict()
        
        assert data["id"] == "enemy_001"
        assert data["name"] == "测试敌人"
        assert data["max_hp"] == 100
        assert data["speed"] == 1.5

    def test_frozen_dto_is_immutable(self):
        """测试 DTO 是不可变的"""
        enemy = EnemyConfigDTO(
            id="enemy_001",
            name="测试敌人",
            max_hp=100,
            speed=1.5,
            damage=10,
            reward=5
        )
        
        with pytest.raises(FrozenInstanceError):
            enemy.max_hp = 200

    def test_repr_contains_all_fields(self):
        """测试 __repr__ 包含所有字段"""
        enemy = EnemyConfigDTO(
            id="enemy_001",
            name="测试敌人",
            max_hp=100,
            speed=1.5,
            damage=10,
            reward=5
        )
        
        repr_str = repr(enemy)
        
        assert "enemy_001" in repr_str
        assert "测试敌人" in repr_str
        assert "max_hp=100" in repr_str


class TestEnemyConfigDTO:
    """测试敌人配置 DTO"""

    def test_enemy_config_creation(self):
        """测试敌人配置创建"""
        enemy = EnemyConfigDTO(
            id="enemy_basic_001",
            name="基础影裔",
            max_hp=100,
            speed=1.5,
            damage=10,
            reward=10,
            description="测试敌人"
        )
        
        assert enemy.id == "enemy_basic_001"
        assert enemy.name == "基础影裔"
        assert enemy.max_hp == 100
        assert enemy.speed == 1.5
        assert enemy.damage == 10
        assert enemy.reward == 10

    def test_description_default_empty(self):
        """测试描述默认值为空字符串"""
        enemy = EnemyConfigDTO(
            id="enemy_001",
            name="敌人",
            max_hp=100,
            speed=1.0,
            damage=5,
            reward=5
        )
        
        assert enemy.description == ""


class TestTowerConfigDTO:
    """测试防御塔配置 DTO"""

    def test_tower_config_creation(self):
        """测试防御塔配置创建"""
        tower = TowerConfigDTO(
            id="tower_arrow_001",
            name="箭塔",
            cost=100,
            damage=20,
            attack_range=3.0,
            attack_speed=1.0,
            description="测试防御塔",
            upgrade_ids=["tower_arrow_002"]
        )
        
        assert tower.id == "tower_arrow_001"
        assert tower.name == "箭塔"
        assert tower.cost == 100
        assert tower.damage == 20
        assert tower.attack_range == 3.0
        assert tower.attack_speed == 1.0

    def test_upgrade_ids_default_empty(self):
        """测试升级 ID 列表默认值为空"""
        tower = TowerConfigDTO(
            id="tower_001",
            name="测试塔",
            cost=100,
            damage=10,
            attack_range=2.0,
            attack_speed=1.0
        )
        
        assert tower.upgrade_ids == []


class TestWaveConfigDTO:
    """测试波次配置 DTO"""

    def test_wave_config_creation(self):
        """测试波次配置创建"""
        wave = WaveConfigDTO(
            id="wave_01_001",
            name="第一关 第一波",
            level_id="level_001",
            wave_number=1,
            enemy_spawns=[
                EnemySpawnConfig(
                    enemy_id="enemy_basic_001",
                    count=5,
                    spawn_interval=1.5
                )
            ],
            reward=50
        )
        
        assert wave.id == "wave_01_001"
        assert wave.level_id == "level_001"
        assert wave.wave_number == 1
        assert len(wave.enemy_spawns) == 1
        assert wave.reward == 50

    def test_enemy_spawn_config(self):
        """测试敌人生成配置"""
        spawn = EnemySpawnConfig(
            enemy_id="enemy_001",
            count=10,
            spawn_interval=2.0,
            delay_before=5.0
        )
        
        assert spawn.enemy_id == "enemy_001"
        assert spawn.count == 10
        assert spawn.spawn_interval == 2.0
        assert spawn.delay_before == 5.0

    def test_from_dict_with_enemy_spawns(self):
        """测试从字典创建波次配置（包含敌人生成列表）"""
        data = {
            "id": "wave_001",
            "name": "测试波次",
            "level_id": "level_001",
            "wave_number": 1,
            "enemy_spawns": [
                {
                    "enemy_id": "enemy_001",
                    "count": 5,
                    "spawn_interval": 1.0
                }
            ],
            "reward": 100
        }
        
        wave = WaveConfigDTO.from_dict(data)
        
        assert len(wave.enemy_spawns) == 1
        assert isinstance(wave.enemy_spawns[0], EnemySpawnConfig)
        assert wave.enemy_spawns[0].enemy_id == "enemy_001"


class TestMockDataLoader:
    """测试模拟数据加载器"""

    def setup_method(self):
        """每个测试方法前重置 ServiceLocator"""
        ServiceLocator.reset()

    def test_load_enemy_config(self):
        """测试加载单个敌人配置"""
        loader = MockDataLoader()
        
        enemy = loader.load_enemy_config("enemy_basic_001")
        
        assert enemy is not None
        assert enemy.id == "enemy_basic_001"
        assert enemy.name == "基础影裔"

    def test_load_nonexistent_enemy_returns_none(self):
        """测试加载不存在的敌人返回 None"""
        loader = MockDataLoader()
        
        enemy = loader.load_enemy_config("nonexistent")
        
        assert enemy is None

    def test_load_tower_config(self):
        """测试加载单个防御塔配置"""
        loader = MockDataLoader()
        
        tower = loader.load_tower_config("tower_arrow_001")
        
        assert tower is not None
        assert tower.id == "tower_arrow_001"
        assert tower.name == "箭塔"

    def test_load_wave_config(self):
        """测试加载单个波次配置"""
        loader = MockDataLoader()
        
        wave = loader.load_wave_config("wave_01_001")
        
        assert wave is not None
        assert wave.id == "wave_01_001"
        assert wave.name == "第一关 第一波"

    def test_load_all_enemy_configs(self):
        """测试加载所有敌人配置"""
        loader = MockDataLoader()
        
        enemies = loader.load_all_enemy_configs()
        
        assert len(enemies) >= 3
        enemy_ids = {e.id for e in enemies}
        assert "enemy_basic_001" in enemy_ids
        assert "enemy_fast_001" in enemy_ids
        assert "enemy_tank_001" in enemy_ids

    def test_load_all_tower_configs(self):
        """测试加载所有防御塔配置"""
        loader = MockDataLoader()
        
        towers = loader.load_all_tower_configs()
        
        assert len(towers) >= 3
        tower_ids = {t.id for t in towers}
        assert "tower_arrow_001" in tower_ids
        assert "tower_cannon_001" in tower_ids
        assert "tower_ice_001" in tower_ids

    def test_load_all_wave_configs(self):
        """测试加载所有波次配置"""
        loader = MockDataLoader()
        
        waves = loader.load_all_wave_configs()
        
        assert len(waves) >= 3
        wave_ids = {w.id for w in waves}
        assert "wave_01_001" in wave_ids
        assert "wave_01_002" in wave_ids
        assert "wave_01_003" in wave_ids

    def test_load_wave_configs_by_level(self):
        """测试按关卡加载波次配置"""
        loader = MockDataLoader()
        
        waves = loader.load_wave_configs_by_level("level_001")
        
        assert len(waves) == 3
        assert waves[0].wave_number == 1
        assert waves[1].wave_number == 2
        assert waves[2].wave_number == 3

    def test_load_wave_configs_by_nonexistent_level(self):
        """测试加载不存在关卡的波次"""
        loader = MockDataLoader()
        
        waves = loader.load_wave_configs_by_level("nonexistent")
        
        assert waves == []

    def test_mock_loader_implements_idataloader(self):
        """测试 MockDataLoader 实现了 IDataLoader 接口"""
        loader = MockDataLoader()
        
        assert isinstance(loader, IDataLoader)

    def test_register_with_service_locator(self):
        """测试通过 ServiceLocator 使用数据加载器"""
        loader = MockDataLoader()
        register_service(IDataLoader, loader)
        
        retrieved = get_service(IDataLoader)
        
        assert retrieved is loader
        enemy = retrieved.load_enemy_config("enemy_basic_001")
        assert enemy.name == "基础影裔"
