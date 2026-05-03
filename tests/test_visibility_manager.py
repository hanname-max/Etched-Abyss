"""
黑雾机制测试

测试 GridCell.is_visible、GridMap 可见性方法和 VisibilityManager。
"""

import pytest

from CoreLogic.SpaceMapping.GridCell import GridCell
from CoreLogic.SpaceMapping.GridMap import GridMap
from CoreLogic.Managers.VisibilityManager import VisibilityManager
from CoreLogic.Core.ServiceLocator import register_service, ServiceLocator


class TestGridCellVisibility:
    """测试 GridCell 的 is_visible 属性"""
    
    def setup_method(self):
        """每个测试前的准备"""
        ServiceLocator.reset()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
    
    def test_default_is_visible_is_false(self):
        """测试默认 is_visible 为 False（被黑雾笼罩）"""
        cell = GridCell(x=0, y=0)
        
        assert cell.is_visible is False
        assert cell.x == 0
        assert cell.y == 0
        assert cell.is_walkable is True
    
    def test_custom_is_visible_true(self):
        """测试设置 is_visible 为 True（黑雾消散）"""
        cell = GridCell(x=5, y=3, is_visible=True)
        
        assert cell.is_visible is True
        assert cell.is_walkable is True
    
    def test_custom_is_visible_false(self):
        """测试显式设置 is_visible 为 False"""
        cell = GridCell(x=5, y=3, is_visible=False)
        
        assert cell.is_visible is False
    
    def test_frozen_immutable(self):
        """测试 GridCell 是不可变的"""
        cell = GridCell(x=0, y=0)
        
        with pytest.raises(AttributeError):
            cell.is_visible = True
        
        with pytest.raises(AttributeError):
            cell.x = 5
    
    def test_equality_with_visibility(self):
        """测试相等性比较包含 is_visible"""
        cell1 = GridCell(x=0, y=0, is_visible=False)
        cell2 = GridCell(x=0, y=0, is_visible=False)
        cell3 = GridCell(x=0, y=0, is_visible=True)
        
        assert cell1 == cell2
        assert cell1 != cell3
    
    def test_hash_includes_visibility(self):
        """测试哈希值包含 is_visible"""
        cell1 = GridCell(x=0, y=0, is_visible=False)
        cell2 = GridCell(x=0, y=0, is_visible=False)
        cell3 = GridCell(x=0, y=0, is_visible=True)
        
        assert hash(cell1) == hash(cell2)
        assert hash(cell1) != hash(cell3)


class TestGridMapVisibility:
    """测试 GridMap 的可见性相关方法"""
    
    def setup_method(self):
        """每个测试前的准备"""
        ServiceLocator.reset()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
    
    def test_all_cells_hidden_by_default(self):
        """测试所有格子默认被黑雾笼罩"""
        grid_map = GridMap(width=5, height=5)
        
        visible_cells = grid_map.get_visible_cells()
        hidden_cells = grid_map.get_hidden_cells()
        
        assert len(visible_cells) == 0
        assert len(hidden_cells) == 25
        
        for cell in grid_map:
            assert cell.is_visible is False
    
    def test_set_visible(self):
        """测试设置单个格子的可见性"""
        grid_map = GridMap(width=5, height=5)
        
        result = grid_map.set_visible(2, 2, True)
        assert result is True
        
        cell = grid_map.get_cell(2, 2)
        assert cell is not None
        assert cell.is_visible is True
        
        assert len(grid_map.get_visible_cells()) == 1
        assert len(grid_map.get_hidden_cells()) == 24
    
    def test_set_visible_out_of_bounds(self):
        """测试设置越界位置的可见性返回 False"""
        grid_map = GridMap(width=5, height=5)
        
        result1 = grid_map.set_visible(-1, 2, True)
        result2 = grid_map.set_visible(10, 2, True)
        result3 = grid_map.set_visible(2, -1, True)
        result4 = grid_map.set_visible(2, 10, True)
        
        assert result1 is False
        assert result2 is False
        assert result3 is False
        assert result4 is False
    
    def test_is_visible(self):
        """测试检查单个格子的可见性"""
        grid_map = GridMap(width=5, height=5)
        
        assert grid_map.is_visible(2, 2) is False
        
        grid_map.set_visible(2, 2, True)
        
        assert grid_map.is_visible(2, 2) is True
    
    def test_is_visible_out_of_bounds(self):
        """测试检查越界位置的可见性返回 None"""
        grid_map = GridMap(width=5, height=5)
        
        assert grid_map.is_visible(-1, 2) is None
        assert grid_map.is_visible(10, 2) is None
    
    def test_set_visible_preserves_walkable(self):
        """测试设置可见性不影响可通行性"""
        grid_map = GridMap(width=5, height=5)
        
        grid_map.set_walkable(2, 2, False)
        
        cell_before = grid_map.get_cell(2, 2)
        assert cell_before is not None
        assert cell_before.is_walkable is False
        assert cell_before.is_visible is False
        
        grid_map.set_visible(2, 2, True)
        
        cell_after = grid_map.get_cell(2, 2)
        assert cell_after is not None
        assert cell_after.is_walkable is False
        assert cell_after.is_visible is True
    
    def test_set_walkable_preserves_visible(self):
        """测试设置可通行性不影响可见性"""
        grid_map = GridMap(width=5, height=5)
        
        grid_map.set_visible(2, 2, True)
        
        cell_before = grid_map.get_cell(2, 2)
        assert cell_before is not None
        assert cell_before.is_visible is True
        assert cell_before.is_walkable is True
        
        grid_map.set_walkable(2, 2, False)
        
        cell_after = grid_map.get_cell(2, 2)
        assert cell_after is not None
        assert cell_after.is_visible is True
        assert cell_after.is_walkable is False
    
    def test_get_visible_cells(self):
        """测试获取所有可见格子"""
        grid_map = GridMap(width=3, height=3)
        
        grid_map.set_visible(0, 0, True)
        grid_map.set_visible(1, 1, True)
        grid_map.set_visible(2, 2, True)
        
        visible = grid_map.get_visible_cells()
        
        assert len(visible) == 3
        
        visible_set = {(cell.x, cell.y) for cell in visible}
        assert (0, 0) in visible_set
        assert (1, 1) in visible_set
        assert (2, 2) in visible_set
    
    def test_get_hidden_cells(self):
        """测试获取所有隐藏格子"""
        grid_map = GridMap(width=3, height=3)
        
        grid_map.set_visible(1, 1, True)
        
        hidden = grid_map.get_hidden_cells()
        
        assert len(hidden) == 8
        
        hidden_set = {(cell.x, cell.y) for cell in hidden}
        assert (1, 1) not in hidden_set
    
    def test_reset_visibility(self):
        """测试重置可见性"""
        grid_map = GridMap(width=3, height=3)
        
        for x in range(3):
            for y in range(3):
                grid_map.set_visible(x, y, True)
        
        assert len(grid_map.get_visible_cells()) == 9
        
        grid_map.reset_visibility()
        
        assert len(grid_map.get_visible_cells()) == 0
        assert len(grid_map.get_hidden_cells()) == 9
    
    def test_reset_visibility_preserves_walkable(self):
        """测试重置可见性保留可通行性"""
        grid_map = GridMap(width=3, height=3)
        
        grid_map.set_walkable(1, 1, False)
        grid_map.set_visible(1, 1, True)
        
        cell_before = grid_map.get_cell(1, 1)
        assert cell_before is not None
        assert cell_before.is_walkable is False
        assert cell_before.is_visible is True
        
        grid_map.reset_visibility()
        
        cell_after = grid_map.get_cell(1, 1)
        assert cell_after is not None
        assert cell_after.is_walkable is False
        assert cell_after.is_visible is False
    
    def test_reset_sets_all_hidden(self):
        """测试 reset() 方法将所有格子设为隐藏"""
        grid_map = GridMap(width=3, height=3)
        
        for x in range(3):
            for y in range(3):
                grid_map.set_visible(x, y, True)
        
        assert len(grid_map.get_visible_cells()) == 9
        
        grid_map.reset()
        
        assert len(grid_map.get_visible_cells()) == 0
    
    def test_resize_sets_all_hidden(self):
        """测试 resize() 方法将新格子设为隐藏"""
        grid_map = GridMap(width=3, height=3)
        
        for x in range(3):
            for y in range(3):
                grid_map.set_visible(x, y, True)
        
        assert len(grid_map.get_visible_cells()) == 9
        
        grid_map.resize(5, 5)
        
        assert len(grid_map.get_visible_cells()) == 0


class TestVisibilityManager:
    """测试 VisibilityManager"""
    
    def setup_method(self):
        """每个测试前的准备"""
        ServiceLocator.reset()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
    
    def _setup_grid_map(self, width=10, height=10):
        """创建并注册 GridMap"""
        grid_map = GridMap(width=width, height=height)
        register_service(GridMap, grid_map)
        return grid_map
    
    def test_check_visibility_no_grid_map(self):
        """测试没有 GridMap 时 check_visibility 返回 False"""
        vm = VisibilityManager()
        
        result = vm.check_visibility(5, 5)
        
        assert result is False
    
    def test_check_visibility_hidden(self):
        """测试检查被黑雾笼罩的位置"""
        self._setup_grid_map(width=10, height=10)
        vm = VisibilityManager()
        
        result = vm.check_visibility(5, 5)
        
        assert result is False
    
    def test_check_visibility_visible(self):
        """测试检查已探索的位置"""
        grid_map = self._setup_grid_map(width=10, height=10)
        grid_map.set_visible(5, 5, True)
        
        vm = VisibilityManager()
        
        result = vm.check_visibility(5, 5)
        
        assert result is True
    
    def test_update_light_source_adding(self):
        """测试添加光源"""
        self._setup_grid_map(width=10, height=10)
        vm = VisibilityManager()
        
        affected = vm.update_light_source(5, 5, radius=2, is_adding=True)
        
        assert affected > 0
        assert vm.check_visibility(5, 5) is True
        assert vm.check_visibility(4, 5) is True
        assert vm.check_visibility(6, 5) is True
        assert vm.check_visibility(5, 4) is True
        assert vm.check_visibility(5, 6) is True
    
    def test_update_light_source_radius_zero(self):
        """测试半径为 0 的光源"""
        self._setup_grid_map(width=10, height=10)
        vm = VisibilityManager()
        
        affected = vm.update_light_source(5, 5, radius=0, is_adding=True)
        
        assert affected == 1
        assert vm.check_visibility(5, 5) is True
        assert vm.check_visibility(4, 5) is False
    
    def test_light_source_manhattan_distance(self):
        """测试光源使用曼哈顿距离计算半径"""
        self._setup_grid_map(width=10, height=10)
        vm = VisibilityManager()
        
        vm.update_light_source(5, 5, radius=2, is_adding=True)
        
        assert vm.check_visibility(5, 5) is True
        assert vm.check_visibility(7, 5) is True
        assert vm.check_visibility(5, 7) is True
        
        assert vm.check_visibility(7, 6) is False
        
        assert vm.check_visibility(6, 6) is True
    
    def test_update_light_source_removing(self):
        """测试移除光源"""
        grid_map = self._setup_grid_map(width=10, height=10)
        vm = VisibilityManager()
        
        vm.update_light_source(5, 5, radius=2, is_adding=True)
        
        assert vm.check_visibility(5, 5) is True
        assert vm.get_visible_count() > 0
        
        vm.update_light_source(5, 5, radius=2, is_adding=False)
        
        assert vm.check_visibility(5, 5) is False
        assert vm.get_visible_count() == 0
    
    def test_add_multiple_sources(self):
        """测试添加多个光源"""
        self._setup_grid_map(width=10, height=10)
        vm = VisibilityManager()
        
        vm.update_light_source(3, 3, radius=1, is_adding=True)
        vm.update_light_source(7, 7, radius=1, is_adding=True)
        
        assert vm.check_visibility(3, 3) is True
        assert vm.check_visibility(7, 7) is True
        assert vm.check_visibility(2, 3) is True
        assert vm.check_visibility(8, 7) is True
        
        assert vm.get_active_source_count() == 2
    
    def test_remove_one_source_keeps_other(self):
        """测试移除一个光源后，另一个光源的影响仍然存在"""
        self._setup_grid_map(width=10, height=10)
        vm = VisibilityManager()
        
        vm.update_light_source(3, 3, radius=1, is_adding=True)
        vm.update_light_source(7, 7, radius=1, is_adding=True)
        
        assert vm.check_visibility(3, 3) is True
        assert vm.check_visibility(7, 7) is True
        
        vm.update_light_source(3, 3, radius=1, is_adding=False)
        
        assert vm.check_visibility(3, 3) is False
        assert vm.check_visibility(7, 7) is True
        assert vm.get_active_source_count() == 1
    
    def test_add_light_source_convenience(self):
        """测试 add_light_source 便捷方法"""
        self._setup_grid_map(width=10, height=10)
        vm = VisibilityManager()
        
        affected = vm.add_light_source(5, 5, radius=1)
        
        assert affected > 0
        assert vm.check_visibility(5, 5) is True
    
    def test_remove_light_source_convenience(self):
        """测试 remove_light_source 便捷方法"""
        self._setup_grid_map(width=10, height=10)
        vm = VisibilityManager()
        
        vm.add_light_source(5, 5, radius=1)
        
        assert vm.check_visibility(5, 5) is True
        
        vm.remove_light_source(5, 5, radius=1)
        
        assert vm.check_visibility(5, 5) is False
    
    def test_reveal_all(self):
        """测试揭示全图"""
        grid_map = self._setup_grid_map(width=5, height=5)
        vm = VisibilityManager()
        
        assert vm.get_visible_count() == 0
        
        affected = vm.reveal_all()
        
        assert affected == 25
        assert vm.get_visible_count() == 25
        
        for x in range(5):
            for y in range(5):
                assert vm.check_visibility(x, y) is True
    
    def test_reset_all(self):
        """测试重置所有可见性"""
        grid_map = self._setup_grid_map(width=5, height=5)
        vm = VisibilityManager()
        
        vm.add_light_source(2, 2, radius=5)
        
        assert vm.get_visible_count() > 0
        assert vm.get_active_source_count() == 1
        
        affected = vm.reset_all()
        
        assert affected > 0
        assert vm.get_visible_count() == 0
        assert vm.get_active_source_count() == 0
    
    def test_get_visible_count(self):
        """测试获取可见格子数量"""
        self._setup_grid_map(width=10, height=10)
        vm = VisibilityManager()
        
        assert vm.get_visible_count() == 0
        
        vm.add_light_source(5, 5, radius=1)
        
        assert vm.get_visible_count() > 0
    
    def test_get_hidden_count(self):
        """测试获取隐藏格子数量"""
        self._setup_grid_map(width=10, height=10)
        vm = VisibilityManager()
        
        assert vm.get_hidden_count() == 100
        
        vm.add_light_source(5, 5, radius=1)
        
        assert vm.get_hidden_count() < 100
    
    def test_get_active_source_count(self):
        """测试获取活跃光源数量"""
        self._setup_grid_map(width=10, height=10)
        vm = VisibilityManager()
        
        assert vm.get_active_source_count() == 0
        
        vm.add_light_source(3, 3, radius=1)
        vm.add_light_source(7, 7, radius=1)
        
        assert vm.get_active_source_count() == 2
        
        vm.remove_light_source(3, 3, radius=1)
        
        assert vm.get_active_source_count() == 1


class TestFogOfWarEndToEnd:
    """黑雾机制端到端测试"""
    
    def setup_method(self):
        """每个测试前的准备"""
        ServiceLocator.reset()
    
    def teardown_method(self):
        """每个测试后的清理"""
        ServiceLocator.reset()
    
    def test_full_exploration_scenario(self):
        """测试完整的探索场景"""
        grid_map = GridMap(width=15, height=15)
        register_service(GridMap, grid_map)
        
        vm = VisibilityManager()
        
        for x in range(15):
            for y in range(15):
                assert vm.check_visibility(x, y) is False
        
        vm.add_light_source(3, 3, radius=2)
        
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if abs(dx) + abs(dy) <= 2:
                    assert vm.check_visibility(3 + dx, 3 + dy) is True
        
        vm.add_light_source(10, 10, radius=3)
        
        assert vm.check_visibility(3, 3) is True
        assert vm.check_visibility(10, 10) is True
        assert vm.get_active_source_count() == 2
        
        vm.remove_light_source(3, 3, radius=2)
        
        assert vm.check_visibility(3, 3) is False
        assert vm.check_visibility(10, 10) is True
        assert vm.get_active_source_count() == 1
        
        vm.reveal_all()
        
        assert vm.get_visible_count() == 225
        
        vm.reset_all()
        
        assert vm.get_visible_count() == 0
        assert vm.get_active_source_count() == 0
