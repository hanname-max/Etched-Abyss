"""
网格地图类

GridMap 是二维网格空间映射的核心类，用于承载防御塔和敌人的坐标。
这是一个纯内存数据结构，不涉及任何引擎层的物理碰撞箱或网格渲染代码。
"""

from typing import Dict, Optional, Tuple, List, Iterator
from threading import Lock

from CoreLogic.SpaceMapping.GridCell import GridCell


class GridMap:
    """
    网格地图类。
    
    二维空间映射的核心实现，用于管理游戏地图中的网格单元。
    提供安全的访问接口，处理越界异常，并支持线程安全的并发访问。
    
    核心功能：
    1. 初始化时接收宽度和高度，构建 GridCell 二维数组
    2. 提供安全的访问接口，如 get_cell(x, y)
    3. 处理越界异常，返回 None 而非抛出异常
    4. 支持设置单元的可通行性
    5. 线程安全的并发访问
    
    属性：
        width: 网格地图的宽度（X 方向单元数量）
        height: 网格地图的高度（Y 方向单元数量）
        
    示例：
        # 创建一个 10x10 的网格地图
        grid_map = GridMap(width=10, height=10)
        
        # 获取指定坐标的单元
        cell = grid_map.get_cell(2, 3)
        print(cell)  # GridCell(x=2, y=3, is_walkable=True)
        
        # 设置单元为不可通行（如放置防御塔）
        grid_map.set_walkable(2, 3, False)
        
        # 检查坐标是否在边界内
        is_valid = grid_map.is_valid_position(15, 15)  # False
    """

    def __init__(self, width: int, height: int):
        """
        初始化网格地图。
        
        参数：
            width: 网格地图的宽度（X 方向单元数量），必须大于 0
            height: 网格地图的高度（Y 方向单元数量），必须大于 0
            
        异常：
            ValueError: 如果 width 或 height 小于等于 0
        """
        if width <= 0:
            raise ValueError(f"Width must be greater than 0, got {width}")
        if height <= 0:
            raise ValueError(f"Height must be greater than 0, got {height}")

        self._width: int = width
        self._height: int = height
        
        self._cells: Dict[Tuple[int, int], GridCell] = {}
        self._lock: Lock = Lock()
        
        self._initialize_cells()

    def _initialize_cells(self) -> None:
        """
        初始化所有网格单元。
        
        在构造函数中调用，创建所有 GridCell 实例并存储在字典中。
        所有单元默认都是可通行的（is_walkable=True），默认被黑雾笼罩（is_visible=False）。
        """
        with self._lock:
            for y in range(self._height):
                for x in range(self._width):
                    self._cells[(x, y)] = GridCell(x=x, y=y, is_walkable=True, is_visible=False)

    @property
    def width(self) -> int:
        """返回网格地图的宽度。"""
        return self._width

    @property
    def height(self) -> int:
        """返回网格地图的高度。"""
        return self._height

    def is_valid_position(self, x: int, y: int) -> bool:
        """
        检查指定坐标是否在网格地图的有效范围内。
        
        参数：
            x: 要检查的 X 坐标
            y: 要检查的 Y 坐标
            
        返回：
            True 如果坐标有效；否则返回 False
        """
        return 0 <= x < self._width and 0 <= y < self._height

    def get_cell(self, x: int, y: int) -> Optional[GridCell]:
        """
        获取指定坐标的网格单元。
        
        提供安全的访问接口，处理越界异常。
        如果坐标越界，返回 None 而非抛出异常。
        
        参数：
            x: 要获取的单元的 X 坐标
            y: 要获取的单元的 Y 坐标
            
        返回：
            GridCell 实例如果坐标有效；否则返回 None
            
        线程安全：此方法是线程安全的
        """
        if not self.is_valid_position(x, y):
            return None
        
        with self._lock:
            return self._cells.get((x, y))

    def set_walkable(self, x: int, y: int, is_walkable: bool) -> bool:
        """
        设置指定坐标单元的可通行性。
        保持现有的可见性状态不变。
        
        参数：
            x: 要设置的单元的 X 坐标
            y: 要设置的单元的 Y 坐标
            is_walkable: 新的可通行性状态
            
        返回：
            True 如果设置成功；False 如果坐标越界
            
        线程安全：此方法是线程安全的
        """
        if not self.is_valid_position(x, y):
            return False
        
        with self._lock:
            cell = self._cells.get((x, y))
            if cell is not None:
                self._cells[(x, y)] = GridCell(
                    x=x, 
                    y=y, 
                    is_walkable=is_walkable, 
                    is_visible=cell.is_visible
                )
                return True
            return False

    def set_visible(self, x: int, y: int, is_visible: bool) -> bool:
        """
        设置指定坐标单元的可见性。
        保持现有的可通行性状态不变。
        
        这是黑雾机制的核心方法：
        - is_visible=True 表示该区域已被探索，黑雾消散
        - is_visible=False 表示该区域被黑雾笼罩
        
        参数：
            x: 要设置的单元的 X 坐标
            y: 要设置的单元的 Y 坐标
            is_visible: 新的可见性状态
            
        返回：
            True 如果设置成功；False 如果坐标越界
            
        线程安全：此方法是线程安全的
        """
        if not self.is_valid_position(x, y):
            return False
        
        with self._lock:
            cell = self._cells.get((x, y))
            if cell is not None:
                self._cells[(x, y)] = GridCell(
                    x=x, 
                    y=y, 
                    is_walkable=cell.is_walkable, 
                    is_visible=is_visible
                )
                return True
            return False

    def is_walkable(self, x: int, y: int) -> Optional[bool]:
        """
        检查指定坐标单元是否可通行。
        
        参数：
            x: 要检查的单元的 X 坐标
            y: 要检查的单元的 Y 坐标
            
        返回：
            True 如果可通行；False 如果不可通行；None 如果坐标越界
        """
        cell = self.get_cell(x, y)
        if cell is None:
            return None
        return cell.is_walkable

    def is_visible(self, x: int, y: int) -> Optional[bool]:
        """
        检查指定坐标单元是否可见（未被黑雾笼罩）。
        
        参数：
            x: 要检查的单元的 X 坐标
            y: 要检查的单元的 Y 坐标
            
        返回：
            True 如果可见；False 如果被黑雾笼罩；None 如果坐标越界
        """
        cell = self.get_cell(x, y)
        if cell is None:
            return None
        return cell.is_visible

    def get_all_cells(self) -> List[GridCell]:
        """
        获取所有网格单元的列表。
        
        返回：
            包含所有 GridCell 实例的列表，按 Y 坐标从小到大排序，
            相同 Y 坐标按 X 坐标从小到大排序
            
        线程安全：此方法是线程安全的
        """
        with self._lock:
            return [
                self._cells[(x, y)]
                for y in range(self._height)
                for x in range(self._width)
            ]

    def get_walkable_cells(self) -> List[GridCell]:
        """
        获取所有可通行的网格单元。
        
        返回：
            包含所有 is_walkable=True 的 GridCell 实例的列表
        """
        return [cell for cell in self.get_all_cells() if cell.is_walkable]

    def get_blocked_cells(self) -> List[GridCell]:
        """
        获取所有不可通行的网格单元。
        
        返回：
            包含所有 is_walkable=False 的 GridCell 实例的列表
        """
        return [cell for cell in self.get_all_cells() if not cell.is_walkable]

    def get_visible_cells(self) -> List[GridCell]:
        """
        获取所有可见的网格单元（未被黑雾笼罩）。
        
        返回：
            包含所有 is_visible=True 的 GridCell 实例的列表
        """
        return [cell for cell in self.get_all_cells() if cell.is_visible]

    def get_hidden_cells(self) -> List[GridCell]:
        """
        获取所有被黑雾笼罩的网格单元。
        
        返回：
            包含所有 is_visible=False 的 GridCell 实例的列表
        """
        return [cell for cell in self.get_all_cells() if not cell.is_visible]

    def reset(self) -> None:
        """
        重置网格地图。
        
        将所有单元的可通行性设置为 True（默认状态），
        并将所有单元的可见性设置为 False（黑雾笼罩）。
        
        线程安全：此方法是线程安全的
        """
        with self._lock:
            for y in range(self._height):
                for x in range(self._width):
                    self._cells[(x, y)] = GridCell(
                        x=x, 
                        y=y, 
                        is_walkable=True, 
                        is_visible=False
                    )

    def reset_visibility(self) -> None:
        """
        只重置可见性状态，不影响可通行性。
        
        将所有单元的可见性设置为 False（黑雾笼罩）。
        用于重新迷雾整个地图，而保留地形障碍。
        
        线程安全：此方法是线程安全的
        """
        with self._lock:
            for y in range(self._height):
                for x in range(self._width):
                    cell = self._cells.get((x, y))
                    if cell is not None:
                        self._cells[(x, y)] = GridCell(
                            x=x, 
                            y=y, 
                            is_walkable=cell.is_walkable, 
                            is_visible=False
                        )

    def resize(self, new_width: int, new_height: int) -> None:
        """
        调整网格地图的大小。
        
        此操作会重置所有单元，新单元默认都是可通行的，
        且默认被黑雾笼罩（is_visible=False）。
        
        参数：
            new_width: 新的宽度（必须大于 0）
            new_height: 新的高度（必须大于 0）
            
        异常：
            ValueError: 如果 new_width 或 new_height 小于等于 0
            
        线程安全：此方法是线程安全的
        """
        if new_width <= 0:
            raise ValueError(f"New width must be greater than 0, got {new_width}")
        if new_height <= 0:
            raise ValueError(f"New height must be greater than 0, got {new_height}")

        with self._lock:
            self._width = new_width
            self._height = new_height
            self._cells.clear()
            for y in range(self._height):
                for x in range(self._width):
                    self._cells[(x, y)] = GridCell(
                        x=x, 
                        y=y, 
                        is_walkable=True, 
                        is_visible=False
                    )

    def __getitem__(self, index: Tuple[int, int]) -> Optional[GridCell]:
        """
        支持使用下标操作符访问网格单元。
        
        参数：
            index: (x, y) 坐标元组
            
        返回：
            GridCell 实例如果坐标有效；否则返回 None
            
        示例：
            cell = grid_map[2, 3]  # 等价于 grid_map.get_cell(2, 3)
        """
        if not isinstance(index, tuple) or len(index) != 2:
            raise TypeError("Index must be a tuple of (x, y)")
        x, y = index
        return self.get_cell(x, y)

    def __iter__(self) -> Iterator[GridCell]:
        """
        支持迭代器协议。
        
        返回：
            按顺序遍历所有网格单元的迭代器
        """
        return iter(self.get_all_cells())

    def __len__(self) -> int:
        """
        返回网格单元的总数。
        
        返回：
            width * height
        """
        return self._width * self._height

    def __repr__(self) -> str:
        """返回网格地图的字符串表示。"""
        return f"GridMap(width={self._width}, height={self._height}, cells={len(self._cells)})"
