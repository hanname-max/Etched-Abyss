"""
寻路服务测试用例

测试 Pathfinder 类和 A* 寻路算法的功能。
"""

import pytest
from CoreLogic import (
    GridMap,
    Pathfinder,
)


class TestPathfinder:
    """测试 Pathfinder 寻路服务类。"""

    def setup_method(self):
        """每个测试方法前的准备工作。"""
        self.pathfinder = Pathfinder()

    def test_create_pathfinder(self):
        """测试创建 Pathfinder 实例。"""
        pf = Pathfinder()
        assert pf is not None

    def test_find_path_straight_line(self):
        """测试直线寻路（无障碍）。"""
        grid_map = GridMap(width=5, height=5)
        path = self.pathfinder.find_path(
            start_x=0, start_y=2,
            end_x=4, end_y=2,
            grid_map=grid_map
        )
        
        assert len(path) == 5
        assert path[0] == (0, 2)
        assert path[1] == (1, 2)
        assert path[2] == (2, 2)
        assert path[3] == (3, 2)
        assert path[4] == (4, 2)

    def test_find_path_same_start_end(self):
        """测试起点和终点相同的情况。"""
        grid_map = GridMap(width=5, height=5)
        path = self.pathfinder.find_path(
            start_x=2, start_y=2,
            end_x=2, end_y=2,
            grid_map=grid_map
        )
        
        assert len(path) == 1
        assert path[0] == (2, 2)

    def test_find_path_start_invalid(self):
        """测试起点坐标无效。"""
        grid_map = GridMap(width=5, height=5)
        # 起点超出边界
        path = self.pathfinder.find_path(
            start_x=-1, start_y=2,
            end_x=4, end_y=2,
            grid_map=grid_map
        )
        assert path == []
        
        # 起点不可通行
        grid_map.set_walkable(0, 2, False)
        path = self.pathfinder.find_path(
            start_x=0, start_y=2,
            end_x=4, end_y=2,
            grid_map=grid_map
        )
        assert path == []

    def test_find_path_end_invalid(self):
        """测试终点坐标无效。"""
        grid_map = GridMap(width=5, height=5)
        # 终点超出边界
        path = self.pathfinder.find_path(
            start_x=0, start_y=2,
            end_x=10, end_y=2,
            grid_map=grid_map
        )
        assert path == []
        
        # 终点不可通行
        grid_map.set_walkable(4, 2, False)
        path = self.pathfinder.find_path(
            start_x=0, start_y=2,
            end_x=4, end_y=2,
            grid_map=grid_map
        )
        assert path == []

    def test_find_path_around_obstacle(self):
        """测试绕过障碍物寻路。"""
        grid_map = GridMap(width=5, height=5)
        
        # 在中间设置一排障碍物，只留一个缺口在顶部
        grid_map.set_walkable(2, 1, False)
        grid_map.set_walkable(2, 2, False)
        grid_map.set_walkable(2, 3, False)
        grid_map.set_walkable(2, 4, False)
        
        # 从左边到右边，需要绕路从顶部缺口通过
        path = self.pathfinder.find_path(
            start_x=0, start_y=2,
            end_x=4, end_y=2,
            grid_map=grid_map
        )
        
        # 应该找到路径：需要向上绕到 y=0，然后通过，再下来
        assert len(path) > 0
        assert path[0] == (0, 2)
        assert path[-1] == (4, 2)
        
        # 路径不应该经过被阻塞的单元格
        blocked_coords = [(2, 1), (2, 2), (2, 3), (2, 4)]
        for coord in blocked_coords:
            assert coord not in path

    def test_find_path_completely_blocked(self):
        """测试完全被阻塞，无法找到路径。"""
        grid_map = GridMap(width=5, height=5)
        
        # 创建一堵完全的墙，从 y=0 到 y=4
        for y in range(5):
            grid_map.set_walkable(2, y, False)
        
        # 尝试从左边到右边，应该找不到路径
        path = self.pathfinder.find_path(
            start_x=0, start_y=2,
            end_x=4, end_y=2,
            grid_map=grid_map
        )
        
        assert path == []

    def test_find_path_diagonal_attempt(self):
        """测试确认不支持对角线移动。"""
        grid_map = GridMap(width=3, height=3)
        
        # 设置除了起点和终点外，中间十字被阻塞
        # 这样如果允许对角线，从 (0,0) 可以直接到 (2,2)
        # 但由于只允许上下左右，需要绕路
        grid_map.set_walkable(1, 0, False)
        grid_map.set_walkable(0, 1, False)
        grid_map.set_walkable(1, 1, False)
        grid_map.set_walkable(2, 1, False)
        grid_map.set_walkable(1, 2, False)
        
        path = self.pathfinder.find_path(
            start_x=0, start_y=0,
            end_x=2, end_y=2,
            grid_map=grid_map
        )
        
        # 由于所有中间路都被阻塞，且不允许对角线，应该找不到路径
        assert path == []

    def test_find_path_larger_grid(self):
        """测试在较大网格上寻路。"""
        grid_map = GridMap(width=10, height=10)
        
        # 添加一些随机障碍物
        obstacles = [
            (3, 0), (3, 1), (3, 2), (3, 3),
            (6, 6), (6, 7), (6, 8), (6, 9),
        ]
        for x, y in obstacles:
            grid_map.set_walkable(x, y, False)
        
        path = self.pathfinder.find_path(
            start_x=0, start_y=0,
            end_x=9, end_y=9,
            grid_map=grid_map
        )
        
        # 应该找到路径
        assert len(path) > 0
        assert path[0] == (0, 0)
        assert path[-1] == (9, 9)
        
        # 路径不应该经过障碍物
        for coord in obstacles:
            assert coord not in path

    def test_path_contains_only_walkable_cells(self):
        """测试返回的路径只包含可通行的单元格。"""
        grid_map = GridMap(width=5, height=5)
        
        # 设置一些障碍物
        grid_map.set_walkable(1, 1, False)
        grid_map.set_walkable(2, 2, False)
        grid_map.set_walkable(3, 1, False)
        
        path = self.pathfinder.find_path(
            start_x=0, start_y=0,
            end_x=4, end_y=4,
            grid_map=grid_map
        )
        
        # 验证路径中的每个点都是可通行的
        for x, y in path:
            is_walkable = grid_map.is_walkable(x, y)
            assert is_walkable is True

    def test_path_is_connected(self):
        """测试返回的路径是连续的（相邻点之间只差一格）。"""
        grid_map = GridMap(width=10, height=10)
        
        # 添加一些障碍物迫使路径绕路
        for i in range(8):
            grid_map.set_walkable(4, i, False)
        
        path = self.pathfinder.find_path(
            start_x=0, start_y=0,
            end_x=9, end_y=9,
            grid_map=grid_map
        )
        
        # 验证路径中的每一步都是相邻的（上下左右）
        for i in range(1, len(path)):
            prev_x, prev_y = path[i - 1]
            curr_x, curr_y = path[i]
            
            # 计算曼哈顿距离，应该等于 1（只允许上下左右移动）
            distance = abs(curr_x - prev_x) + abs(curr_y - prev_y)
            assert distance == 1, f"路径不连续：{path[i-1]} -> {path[i]}"
