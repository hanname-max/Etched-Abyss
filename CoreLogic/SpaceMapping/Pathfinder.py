"""
寻路服务类

提供基于网格地图的 A* 寻路算法实现。
这是一个纯算法类，不涉及任何 Entity 或 Component。
"""

from typing import List, Dict, Optional, Tuple
from heapq import heappush, heappop
from dataclasses import dataclass

from CoreLogic.SpaceMapping.GridMap import GridMap


@dataclass
class PathNode:
    """
    寻路节点数据类。
    
    用于 A* 算法中的节点表示，包含坐标、代价信息和父节点引用。
    
    属性：
        x: 节点的 X 坐标
        y: 节点的 Y 坐标
        g: 从起点到当前节点的实际代价
        h: 从当前节点到终点的预估代价（启发函数值）
        parent: 父节点的坐标元组 (x, y)，用于路径回溯
    """
    x: int
    y: int
    g: float
    h: float
    parent: Optional[Tuple[int, int]] = None

    @property
    def f(self) -> float:
        """返回 F 值（G + H）。"""
        return self.g + self.h

    def __lt__(self, other: 'PathNode') -> bool:
        """比较两个节点的 F 值，用于优先队列排序。"""
        return self.f < other.f


class Pathfinder:
    """
    寻路服务类。
    
    提供基于网格地图的 A* 寻路算法实现。
    支持上下左右四个方向移动，只允许在可通行的网格单元上移动。
    
    核心功能：
    1. 实现经典的 A* 寻路算法
    2. 只考虑 GridMap 中 IsWalkable 为 True 的网格
    3. 支持上下左右移动（四方向）
    4. 返回顺序路径点集合，找不到路径返回空集合
    
    示例：
        # 创建寻路器
        pathfinder = Pathfinder()
        
        # 创建网格地图
        grid_map = GridMap(width=10, height=10)
        
        # 寻找路径
        path = pathfinder.find_path(
            start_x=0, start_y=0,
            end_x=9, end_y=9,
            grid_map=grid_map
        )
        
        # path 是一个包含 (x, y) 元组的列表，表示从起点到终点的路径
    """

    # 四个移动方向：上、下、左、右
    _DIRECTIONS: List[Tuple[int, int]] = [
        (0, -1),  # 上
        (0, 1),   # 下
        (-1, 0),  # 左
        (1, 0),   # 右
    ]

    def __init__(self):
        """初始化寻路服务。"""
        pass

    @staticmethod
    def _manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> float:
        """
        计算曼哈顿距离（启发函数）。
        
        对于只允许上下左右移动的网格，曼哈顿距离是最优的启发函数。
        
        参数：
            x1: 第一个点的 X 坐标
            y1: 第一个点的 Y 坐标
            x2: 第二个点的 X 坐标
            y2: 第二个点的 Y 坐标
            
        返回：
            两点之间的曼哈顿距离
        """
        return abs(x1 - x2) + abs(y1 - y2)

    def _is_valid_and_walkable(
        self, 
        x: int, 
        y: int, 
        grid_map: GridMap
    ) -> bool:
        """
        检查指定坐标是否有效且可通行。
        
        参数：
            x: 要检查的 X 坐标
            y: 要检查的 Y 坐标
            grid_map: 网格地图实例
            
        返回：
            True 如果坐标有效且可通行；否则返回 False
        """
        is_walkable = grid_map.is_walkable(x, y)
        return is_walkable is True

    def _reconstruct_path(
        self, 
        nodes: Dict[Tuple[int, int], PathNode], 
        end_x: int, 
        end_y: int
    ) -> List[Tuple[int, int]]:
        """
        从终点回溯到起点，重建路径。
        
        参数：
            nodes: 所有已访问节点的字典，键为 (x, y) 坐标
            end_x: 终点的 X 坐标
            end_y: 终点的 Y 坐标
            
        返回：
            从起点到终点的顺序路径点列表
        """
        path: List[Tuple[int, int]] = []
        current: Tuple[int, int] = (end_x, end_y)
        
        while current is not None:
            path.append(current)
            node = nodes.get(current)
            if node is None:
                break
            current = node.parent
        
        # 反转路径，使其从起点到终点
        path.reverse()
        return path

    def find_path(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        grid_map: GridMap
    ) -> List[Tuple[int, int]]:
        """
        执行 A* 寻路算法，寻找从起点到终点的路径。
        
        参数：
            start_x: 起点的 X 坐标
            start_y: 起点的 Y 坐标
            end_x: 终点的 X 坐标
            end_y: 终点的 Y 坐标
            grid_map: 网格地图实例，用于检查可通行性
            
        返回：
            表示顺序路径点的列表，每个元素是 (x, y) 元组。
            如果找不到路径（被堵死），返回空列表。
            
        注意：
            - 只允许在 IsWalkable 为 True 的网格上移动
            - 只支持上下左右四个方向移动
            - 返回的路径包含起点和终点
            - 如果起点等于终点，返回只包含该点的列表
        """
        # 验证起点和终点是否在地图范围内且可通行
        if not self._is_valid_and_walkable(start_x, start_y, grid_map):
            return []
        
        if not self._is_valid_and_walkable(end_x, end_y, grid_map):
            return []
        
        # 如果起点就是终点，直接返回
        if start_x == end_x and start_y == end_y:
            return [(start_x, start_y)]
        
        # 开放列表：优先队列（最小堆），存储待探索的节点
        open_heap: List[PathNode] = []
        
        # 开放字典：快速检查某个坐标是否在开放列表中
        open_dict: Dict[Tuple[int, int], PathNode] = {}
        
        # 关闭字典：存储已探索的节点
        closed_dict: Dict[Tuple[int, int], PathNode] = {}
        
        # 创建起点节点
        start_node = PathNode(
            x=start_x,
            y=start_y,
            g=0.0,
            h=self._manhattan_distance(start_x, start_y, end_x, end_y),
            parent=None
        )
        
        # 将起点加入开放列表
        heappush(open_heap, start_node)
        open_dict[(start_x, start_y)] = start_node
        
        # 开始 A* 算法主循环
        while open_heap:
            # 从开放列表中取出 F 值最小的节点
            current_node = heappop(open_heap)
            current_coord = (current_node.x, current_node.y)
            
            # 如果该节点已经在关闭列表中，跳过
            if current_coord in closed_dict:
                continue
            
            # 检查是否到达终点
            if current_node.x == end_x and current_node.y == end_y:
                # 重建路径
                closed_dict[current_coord] = current_node
                return self._reconstruct_path(closed_dict, end_x, end_y)
            
            # 将当前节点移入关闭列表
            del open_dict[current_coord]
            closed_dict[current_coord] = current_node
            
            # 探索四个方向的邻居
            for dx, dy in self._DIRECTIONS:
                neighbor_x = current_node.x + dx
                neighbor_y = current_node.y + dy
                neighbor_coord = (neighbor_x, neighbor_y)
                
                # 跳过已在关闭列表中的节点
                if neighbor_coord in closed_dict:
                    continue
                
                # 检查邻居是否可通行
                if not self._is_valid_and_walkable(neighbor_x, neighbor_y, grid_map):
                    continue
                
                # 计算从当前节点到邻居的 G 值
                # 上下左右移动的代价为 1
                tentative_g = current_node.g + 1.0
                
                # 检查邻居是否已在开放列表中
                existing_node = open_dict.get(neighbor_coord)
                
                if existing_node is None:
                    # 邻居不在开放列表中，创建新节点并加入
                    neighbor_node = PathNode(
                        x=neighbor_x,
                        y=neighbor_y,
                        g=tentative_g,
                        h=self._manhattan_distance(neighbor_x, neighbor_y, end_x, end_y),
                        parent=current_coord
                    )
                    heappush(open_heap, neighbor_node)
                    open_dict[neighbor_coord] = neighbor_node
                else:
                    # 邻居已在开放列表中，检查是否有更优的路径
                    if tentative_g < existing_node.g:
                        # 找到更优路径，更新 G 值和父节点
                        # 注意：由于 heapq 不支持直接更新，我们创建一个新节点并推入堆
                        # 旧节点会在后续处理中被忽略（因为已在关闭列表或有更高的 G 值）
                        updated_node = PathNode(
                            x=neighbor_x,
                            y=neighbor_y,
                            g=tentative_g,
                            h=existing_node.h,
                            parent=current_coord
                        )
                        heappush(open_heap, updated_node)
                        open_dict[neighbor_coord] = updated_node
        
        # 无法找到路径
        return []
