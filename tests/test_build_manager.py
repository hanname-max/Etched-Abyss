"""
建造管理器单元测试

测试 BuildManager 的核心功能，包括：
1. 防御塔建造成功流程
2. 各种建造失败场景（网格越界、网格已占用、配置不存在）
3. can_build 预检查功能
4. cancel_build 释放网格功能
"""

import pytest
from typing import Optional

from CoreLogic import (
    ServiceLocator,
    register_service,
    get_service,
    IDataLoader,
    IGameLogger,
    EntityManager,
    GridMap,
    MockDataLoader,
    GameLogger,
    BuildManager,
    TowerConfigDTO,
    TransformComponent,
    TowerComponent,
)


class TestBuildManager:
    """测试建造管理器"""

    def setup_method(self):
        """每个测试方法前重置 ServiceLocator 并注册必要服务"""
        ServiceLocator.reset()
        
        register_service(IDataLoader, MockDataLoader())
        register_service(IGameLogger, GameLogger())
        register_service(EntityManager, EntityManager())
        register_service(GridMap, GridMap(width=10, height=10))
        register_service(BuildManager, BuildManager())

    def test_build_tower_success(self):
        """测试成功建造防御塔"""
        build_manager = get_service(BuildManager)
        grid_map = get_service(GridMap)
        entity_manager = get_service(EntityManager)
        
        assert grid_map.is_walkable(5, 3) is True
        
        tower_entity = build_manager.build_tower("tower_arrow_001", 5, 3)
        
        assert tower_entity is not None
        assert entity_manager.has_entity(tower_entity.entity_id) is True
        
        assert grid_map.is_walkable(5, 3) is False
        
        transform = tower_entity.get_component(TransformComponent)
        assert transform is not None
        assert transform.x == 5.0
        assert transform.y == 3.0
        
        tower_comp = tower_entity.get_component(TowerComponent)
        assert tower_comp is not None
        assert tower_comp.config_id == "tower_arrow_001"
        assert tower_comp.name == "箭塔"
        assert tower_comp.cost == 100
        assert tower_comp.damage == 20
        assert tower_comp.attack_range == 3.0
        assert tower_comp.attack_speed == 1.0

    def test_build_tower_out_of_bounds(self):
        """测试在越界位置建造防御塔"""
        build_manager = get_service(BuildManager)
        grid_map = get_service(GridMap)
        
        tower_entity = build_manager.build_tower("tower_arrow_001", 100, 100)
        
        assert tower_entity is None
        
        tower_entity2 = build_manager.build_tower("tower_arrow_001", -1, 5)
        assert tower_entity2 is None
        
        tower_entity3 = build_manager.build_tower("tower_arrow_001", 5, -1)
        assert tower_entity3 is None

    def test_build_tower_on_occupied_grid(self):
        """测试在已占用的网格上建造防御塔"""
        build_manager = get_service(BuildManager)
        grid_map = get_service(GridMap)
        
        tower1 = build_manager.build_tower("tower_arrow_001", 5, 3)
        assert tower1 is not None
        assert grid_map.is_walkable(5, 3) is False
        
        tower2 = build_manager.build_tower("tower_cannon_001", 5, 3)
        assert tower2 is None
        
        assert grid_map.is_walkable(5, 3) is False

    def test_build_tower_with_nonexistent_config(self):
        """测试使用不存在的防御塔配置建造"""
        build_manager = get_service(BuildManager)
        grid_map = get_service(GridMap)
        
        original_walkable = grid_map.is_walkable(5, 3)
        assert original_walkable is True
        
        tower_entity = build_manager.build_tower("nonexistent_tower_id", 5, 3)
        
        assert tower_entity is None
        
        assert grid_map.is_walkable(5, 3) is True

    def test_can_build_success(self):
        """测试 can_build 预检查成功"""
        build_manager = get_service(BuildManager)
        
        assert build_manager.can_build(5, 3) is True
        assert build_manager.can_build(0, 0) is True
        assert build_manager.can_build(9, 9) is True

    def test_can_build_out_of_bounds(self):
        """测试 can_build 在越界位置返回 False"""
        build_manager = get_service(BuildManager)
        
        assert build_manager.can_build(10, 5) is False
        assert build_manager.can_build(5, 10) is False
        assert build_manager.can_build(-1, 5) is False
        assert build_manager.can_build(5, -1) is False

    def test_can_build_on_occupied(self):
        """测试 can_build 在已占用网格返回 False"""
        build_manager = get_service(BuildManager)
        
        assert build_manager.can_build(5, 3) is True
        
        build_manager.build_tower("tower_arrow_001", 5, 3)
        
        assert build_manager.can_build(5, 3) is False

    def test_cancel_build(self):
        """测试取消建造（释放网格）"""
        build_manager = get_service(BuildManager)
        grid_map = get_service(GridMap)
        
        build_manager.build_tower("tower_arrow_001", 5, 3)
        assert grid_map.is_walkable(5, 3) is False
        
        success = build_manager.cancel_build(5, 3)
        assert success is True
        assert grid_map.is_walkable(5, 3) is True

    def test_cancel_build_out_of_bounds(self):
        """测试在越界位置取消建造"""
        build_manager = get_service(BuildManager)
        
        success = build_manager.cancel_build(100, 100)
        assert success is False

    def test_multiple_towers_on_different_grids(self):
        """测试在不同网格建造多个防御塔"""
        build_manager = get_service(BuildManager)
        grid_map = get_service(GridMap)
        entity_manager = get_service(EntityManager)
        
        tower1 = build_manager.build_tower("tower_arrow_001", 2, 2)
        tower2 = build_manager.build_tower("tower_cannon_001", 5, 5)
        tower3 = build_manager.build_tower("tower_ice_001", 7, 7)
        
        assert tower1 is not None
        assert tower2 is not None
        assert tower3 is not None
        
        assert grid_map.is_walkable(2, 2) is False
        assert grid_map.is_walkable(5, 5) is False
        assert grid_map.is_walkable(7, 7) is False
        
        assert entity_manager.get_entity_count() == 3
        
        tower1_comp = tower1.get_component(TowerComponent)
        tower2_comp = tower2.get_component(TowerComponent)
        tower3_comp = tower3.get_component(TowerComponent)
        
        assert tower1_comp.name == "箭塔"
        assert tower2_comp.name == "炮塔"
        assert tower3_comp.name == "冰霜塔"

    def test_tower_component_has_upgrade_ids(self):
        """测试 TowerComponent 正确复制 upgrade_ids"""
        build_manager = get_service(BuildManager)
        
        tower_entity = build_manager.build_tower("tower_arrow_001", 5, 3)
        tower_comp = tower_entity.get_component(TowerComponent)
        
        assert tower_comp.upgrade_ids is not None
        assert "tower_arrow_002" in tower_comp.upgrade_ids
        assert "tower_cannon_001" in tower_comp.upgrade_ids

    def test_build_manager_not_registered(self):
        """测试依赖服务未注册时的行为"""
        ServiceLocator.reset()
        
        incomplete_manager = BuildManager()
        
        result = incomplete_manager.build_tower("tower_arrow_001", 5, 3)
        
        assert result is None

    def test_can_build_without_services(self):
        """测试 can_build 在服务未注册时返回 False"""
        ServiceLocator.reset()
        
        incomplete_manager = BuildManager()
        
        result = incomplete_manager.can_build(5, 3)
        
        assert result is False

    def test_cancel_build_without_services(self):
        """测试 cancel_build 在服务未注册时返回 False"""
        ServiceLocator.reset()
        
        incomplete_manager = BuildManager()
        
        result = incomplete_manager.cancel_build(5, 3)
        
        assert result is False
