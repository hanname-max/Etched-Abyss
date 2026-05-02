"""
网格地图测试用例

测试 GridCell 和 GridMap 类的功能。
"""

import pytest
from CoreLogic import (
    GridCell,
    GridMap,
    ServiceLocator,
    register_service,
    get_service,
    is_service_registered,
)


class TestGridCell:
    """测试 GridCell 数据类。"""

    def test_create_grid_cell_default(self):
        """测试创建默认可通行的网格单元。"""
        cell = GridCell(x=0, y=0)
        assert cell.x == 0
        assert cell.y == 0
        assert cell.is_walkable is True

    def test_create_grid_cell_blocked(self):
        """测试创建不可通行的网格单元。"""
        cell = GridCell(x=5, y=3, is_walkable=False)
        assert cell.x == 5
        assert cell.y == 3
        assert cell.is_walkable is False

    def test_grid_cell_equality(self):
        """测试网格单元的相等性比较。"""
        cell1 = GridCell(x=1, y=2, is_walkable=True)
        cell2 = GridCell(x=1, y=2, is_walkable=True)
        cell3 = GridCell(x=1, y=2, is_walkable=False)
        cell4 = GridCell(x=2, y=2, is_walkable=True)

        assert cell1 == cell2
        assert cell1 != cell3
        assert cell1 != cell4
        assert cell1 != "not a cell"

    def test_grid_cell_hash(self):
        """测试网格单元的哈希值。"""
        cell1 = GridCell(x=1, y=2, is_walkable=True)
        cell2 = GridCell(x=1, y=2, is_walkable=True)

        assert hash(cell1) == hash(cell2)

        cell_set = {cell1}
        assert cell2 in cell_set

    def test_grid_cell_repr(self):
        """测试网格单元的字符串表示。"""
        cell = GridCell(x=3, y=5, is_walkable=False)
        repr_str = repr(cell)
        assert "x=3" in repr_str
        assert "y=5" in repr_str
        assert "is_walkable=False" in repr_str


class TestGridMap:
    """测试 GridMap 类。"""

    def test_create_grid_map(self):
        """测试创建网格地图。"""
        grid_map = GridMap(width=10, height=8)
        assert grid_map.width == 10
        assert grid_map.height == 8
        assert len(grid_map) == 80

    def test_create_grid_map_invalid_width(self):
        """测试创建宽度无效的网格地图。"""
        with pytest.raises(ValueError, match="Width must be greater than 0"):
            GridMap(width=0, height=10)

        with pytest.raises(ValueError, match="Width must be greater than 0"):
            GridMap(width=-5, height=10)

    def test_create_grid_map_invalid_height(self):
        """测试创建高度无效的网格地图。"""
        with pytest.raises(ValueError, match="Height must be greater than 0"):
            GridMap(width=10, height=0)

        with pytest.raises(ValueError, match="Height must be greater than 0"):
            GridMap(width=10, height=-3)

    def test_get_cell_valid(self):
        """测试获取有效坐标的单元。"""
        grid_map = GridMap(width=5, height=5)

        cell = grid_map.get_cell(2, 3)
        assert cell is not None
        assert cell.x == 2
        assert cell.y == 3
        assert cell.is_walkable is True

    def test_get_cell_invalid(self):
        """测试获取无效坐标的单元。"""
        grid_map = GridMap(width=5, height=5)

        assert grid_map.get_cell(-1, 0) is None
        assert grid_map.get_cell(0, -1) is None
        assert grid_map.get_cell(5, 0) is None
        assert grid_map.get_cell(0, 5) is None
        assert grid_map.get_cell(100, 100) is None

    def test_is_valid_position(self):
        """测试坐标有效性检查。"""
        grid_map = GridMap(width=10, height=8)

        assert grid_map.is_valid_position(0, 0) is True
        assert grid_map.is_valid_position(9, 7) is True
        assert grid_map.is_valid_position(5, 5) is True

        assert grid_map.is_valid_position(-1, 0) is False
        assert grid_map.is_valid_position(0, -1) is False
        assert grid_map.is_valid_position(10, 0) is False
        assert grid_map.is_valid_position(0, 8) is False

    def test_set_walkable(self):
        """测试设置单元的可通行性。"""
        grid_map = GridMap(width=5, height=5)

        assert grid_map.is_walkable(2, 2) is True

        result = grid_map.set_walkable(2, 2, False)
        assert result is True
        assert grid_map.is_walkable(2, 2) is False

        result = grid_map.set_walkable(2, 2, True)
        assert result is True
        assert grid_map.is_walkable(2, 2) is True

    def test_set_walkable_invalid_position(self):
        """测试设置无效坐标的可通行性。"""
        grid_map = GridMap(width=5, height=5)

        result = grid_map.set_walkable(10, 10, False)
        assert result is False

    def test_is_walkable_invalid_position(self):
        """测试检查无效坐标的可通行性。"""
        grid_map = GridMap(width=5, height=5)

        assert grid_map.is_walkable(10, 10) is None

    def test_get_all_cells(self):
        """测试获取所有单元。"""
        grid_map = GridMap(width=3, height=2)

        all_cells = grid_map.get_all_cells()
        assert len(all_cells) == 6

        expected_coords = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)]
        actual_coords = [(cell.x, cell.y) for cell in all_cells]

        assert actual_coords == expected_coords

    def test_get_walkable_and_blocked_cells(self):
        """测试获取可通行和不可通行的单元。"""
        grid_map = GridMap(width=3, height=3)

        assert len(grid_map.get_walkable_cells()) == 9
        assert len(grid_map.get_blocked_cells()) == 0

        grid_map.set_walkable(0, 0, False)
        grid_map.set_walkable(1, 1, False)
        grid_map.set_walkable(2, 2, False)

        assert len(grid_map.get_walkable_cells()) == 6
        assert len(grid_map.get_blocked_cells()) == 3

    def test_reset(self):
        """测试重置网格地图。"""
        grid_map = GridMap(width=3, height=3)

        grid_map.set_walkable(0, 0, False)
        grid_map.set_walkable(1, 1, False)
        grid_map.set_walkable(2, 2, False)

        assert len(grid_map.get_blocked_cells()) == 3

        grid_map.reset()

        assert len(grid_map.get_blocked_cells()) == 0
        assert len(grid_map.get_walkable_cells()) == 9

    def test_resize(self):
        """测试调整网格地图大小。"""
        grid_map = GridMap(width=5, height=5)
        assert grid_map.width == 5
        assert grid_map.height == 5
        assert len(grid_map) == 25

        grid_map.resize(new_width=10, new_height=8)
        assert grid_map.width == 10
        assert grid_map.height == 8
        assert len(grid_map) == 80

    def test_resize_invalid(self):
        """测试调整为无效大小。"""
        grid_map = GridMap(width=5, height=5)

        with pytest.raises(ValueError, match="New width must be greater than 0"):
            grid_map.resize(new_width=0, new_height=5)

        with pytest.raises(ValueError, match="New height must be greater than 0"):
            grid_map.resize(new_width=5, new_height=0)

    def test_index_operator(self):
        """测试下标操作符访问。"""
        grid_map = GridMap(width=5, height=5)

        cell = grid_map[2, 3]
        assert cell is not None
        assert cell.x == 2
        assert cell.y == 3

        assert grid_map[10, 10] is None

    def test_index_operator_invalid_type(self):
        """测试下标操作符使用无效类型。"""
        grid_map = GridMap(width=5, height=5)

        with pytest.raises(TypeError, match="Index must be a tuple of \\(x, y\\)"):
            _ = grid_map[0]

    def test_iteration(self):
        """测试迭代器协议。"""
        grid_map = GridMap(width=2, height=2)

        cells = list(grid_map)
        assert len(cells) == 4

        expected_coords = [(0, 0), (1, 0), (0, 1), (1, 1)]
        actual_coords = [(cell.x, cell.y) for cell in cells]
        assert actual_coords == expected_coords

    def test_len(self):
        """测试 len() 函数。"""
        grid_map = GridMap(width=10, height=8)
        assert len(grid_map) == 80

    def test_repr(self):
        """测试字符串表示。"""
        grid_map = GridMap(width=10, height=8)
        repr_str = repr(grid_map)
        assert "width=10" in repr_str
        assert "height=8" in repr_str
        assert "cells=80" in repr_str


class TestGridMapIoC:
    """测试 GridMap 作为单例服务注册到 IoC 容器。"""

    def setup_method(self):
        """每个测试方法前重置服务定位器。"""
        ServiceLocator.reset()

    def test_register_grid_map_as_service(self):
        """测试将 GridMap 注册为服务。"""
        grid_map = GridMap(width=20, height=15)
        register_service(GridMap, grid_map)

        assert is_service_registered(GridMap) is True

    def test_get_grid_map_from_service_locator(self):
        """测试从服务定位器获取 GridMap。"""
        original = GridMap(width=20, height=15)
        original.set_walkable(5, 5, False)

        register_service(GridMap, original)

        retrieved = get_service(GridMap)

        assert retrieved is original
        assert retrieved.width == 20
        assert retrieved.height == 15
        assert retrieved.is_walkable(5, 5) is False

    def test_grid_map_singleton_usage(self):
        """测试 GridMap 作为单例的使用场景。"""
        grid_map = GridMap(width=100, height=100)
        register_service(GridMap, grid_map)

        from CoreLogic import get_service as get_svc

        gm1 = get_svc(GridMap)
        gm2 = get_svc(GridMap)

        assert gm1 is gm2

        gm1.set_walkable(10, 10, False)
        assert gm2.is_walkable(10, 10) is False
