"""
可见性管理器

VisibilityManager 统一掌管全图视野的更新，实现黑雾（Fog of War）机制。

============================================================================
【架构规范强制声明】
============================================================================

VisibilityManager 应该通过 ServiceLocator 获取，而不是直接实例化。

正确示例：
    from CoreLogic import get_service, register_service, VisibilityManager

    # 注册到 IoC 容器
    visibility_manager = VisibilityManager()
    register_service(VisibilityManager, visibility_manager)

    # 检查某个位置的可见性
    is_visible = visibility_manager.check_visibility(5, 3)

    # 添加光源（探索一片区域）
    visibility_manager.update_light_source(5, 3, radius=2, is_adding=True)

    # 移除光源
    visibility_manager.update_light_source(5, 3, radius=2, is_adding=False)

错误示例（严禁使用）：
    # 直接实例化多个 VisibilityManager
    vm1 = VisibilityManager()
    vm2 = VisibilityManager()  # 这会导致状态冲突
============================================================================
"""

from typing import List, Tuple, Optional, Dict, Set
from threading import Lock

from CoreLogic.Core.ServiceLocator import try_get_service
from CoreLogic.SpaceMapping.GridMap import GridMap
from CoreLogic.Interfaces.IGameLogger import IGameLogger


class VisibilityManager:
    """
    可见性管理器。

    统一掌管全图视野的更新，实现黑雾（Fog of War）机制。

    核心功能：
    1. 从 IoC 容器获取 GridMap 依赖
    2. 提供 check_visibility(x, y) 接口检查某个位置是否可见
    3. 提供 update_light_source(originX, originY, radius, isAdding) 接口
       - 添加光源时，将指定半径内的 GridCell.is_visible 设为 True
       - 移除光源时，使用引用计数增量更新，不再全图重算
    """

    def __init__(self) -> None:
        self._lock: Lock = Lock()
        # source_key → 覆盖的格子列表（用于移除时增量更新）
        self._source_cells: Dict[Tuple[int, int, int], List[Tuple[int, int]]] = {}
        # 格子坐标 → 覆盖该格子的光源数量（引用计数）
        self._cell_ref_count: Dict[Tuple[int, int], int] = {}
        # source_id → source_key 映射（支持通过 entity_id 管理光源）
        self._id_to_source: Dict[int, Tuple[int, int, int]] = {}

    def _get_grid_map(self) -> Optional[GridMap]:
        return try_get_service(GridMap)

    def _get_logger(self) -> Optional[IGameLogger]:
        return try_get_service(IGameLogger)

    def _log_visibility(self, message: str, **kwargs) -> None:
        logger = self._get_logger()
        if logger is not None:
            logger.info(message, **kwargs)

    def check_visibility(self, x: int, y: int) -> bool:
        grid_map = self._get_grid_map()
        if grid_map is None:
            return False
        is_visible = grid_map.is_visible(x, y)
        return is_visible if is_visible is not None else False

    def update_light_source(self, origin_x: int, origin_y: int, radius: int, is_adding: bool) -> int:
        """
        更新光源，影响指定半径内的所有格子的可见性。

        添加时：遍历半径内格子，引用计数+1，设为可见。
        移除时：只遍历该光源覆盖的格子，引用计数-1，归零才设为不可见。
        """
        grid_map = self._get_grid_map()
        if grid_map is None:
            return 0

        with self._lock:
            if radius < 0:
                radius = 0

            source_key = (origin_x, origin_y, radius)

            if is_adding:
                return self._apply_light_source(grid_map, source_key, origin_x, origin_y, radius)
            else:
                return self._remove_light_source(grid_map, source_key)

    def _apply_light_source(
        self, grid_map: GridMap, source_key: Tuple[int, int, int],
        origin_x: int, origin_y: int, radius: int
    ) -> int:
        if source_key in self._source_cells:
            return 0

        covered_cells: List[Tuple[int, int]] = []
        affected_count = 0

        start_x = max(0, origin_x - radius)
        end_x = min(grid_map.width - 1, origin_x + radius)
        start_y = max(0, origin_y - radius)
        end_y = min(grid_map.height - 1, origin_y + radius)

        for x in range(start_x, end_x + 1):
            for y in range(start_y, end_y + 1):
                distance = abs(x - origin_x) + abs(y - origin_y)
                if distance <= radius:
                    covered_cells.append((x, y))
                    self._cell_ref_count[(x, y)] = self._cell_ref_count.get((x, y), 0) + 1
                    if grid_map.set_visible(x, y, True):
                        affected_count += 1

        self._source_cells[source_key] = covered_cells

        self._log_visibility(
            "应用光源",
            origin_x=origin_x, origin_y=origin_y,
            radius=radius, affected_count=affected_count
        )
        return affected_count

    def _remove_light_source(self, grid_map: GridMap, source_key: Tuple[int, int, int]) -> int:
        covered_cells = self._source_cells.pop(source_key, None)
        if covered_cells is None:
            return 0

        hidden_count = 0
        for x, y in covered_cells:
            ref = self._cell_ref_count.get((x, y), 0) - 1
            if ref <= 0:
                self._cell_ref_count.pop((x, y), None)
                if grid_map.set_visible(x, y, False):
                    hidden_count += 1
            else:
                self._cell_ref_count[(x, y)] = ref

        origin_x, origin_y, radius = source_key
        self._log_visibility(
            "移除光源（增量）",
            origin_x=origin_x, origin_y=origin_y,
            radius=radius, hidden_count=hidden_count
        )
        return hidden_count

    def add_light_source(self, origin_x: int, origin_y: int, radius: int) -> int:
        return self.update_light_source(origin_x, origin_y, radius, is_adding=True)

    def remove_light_source(self, origin_x: int, origin_y: int, radius: int) -> int:
        return self.update_light_source(origin_x, origin_y, radius, is_adding=False)

    def add_light_source_by_id(self, source_id: int, origin_x: int, origin_y: int, radius: int) -> int:
        """通过唯一 ID 添加光源，同一 ID 不会重复添加。"""
        source_key = (origin_x, origin_y, radius)
        with self._lock:
            if source_id in self._id_to_source:
                return 0
            self._id_to_source[source_id] = source_key
        return self.update_light_source(origin_x, origin_y, radius, is_adding=True)

    def remove_light_source_by_id(self, source_id: int) -> int:
        """通过唯一 ID 移除光源，无需知道原始坐标和半径。"""
        with self._lock:
            source_key = self._id_to_source.pop(source_id, None)
            if source_key is None:
                return 0
        return self.update_light_source(source_key[0], source_key[1], source_key[2], is_adding=False)

    def reveal_all(self, grid_map: Optional[GridMap] = None) -> int:
        if grid_map is None:
            grid_map = self._get_grid_map()
        if grid_map is None:
            return 0

        affected_count = 0
        for cell in grid_map.get_all_cells():
            if grid_map.set_visible(cell.x, cell.y, True):
                affected_count += 1

        self._log_visibility("揭示全图", affected_count=affected_count)
        return affected_count

    def reset_all(self, grid_map: Optional[GridMap] = None) -> int:
        if grid_map is None:
            grid_map = self._get_grid_map()
        if grid_map is None:
            return 0

        with self._lock:
            original_visible = len(self._cell_ref_count)
            self._source_cells.clear()
            self._cell_ref_count.clear()
            self._id_to_source.clear()
            grid_map.reset_visibility()

        self._log_visibility("重置所有可见性", original_visible=original_visible)
        return original_visible

    def get_visible_count(self) -> int:
        grid_map = self._get_grid_map()
        if grid_map is None:
            return 0
        return len(grid_map.get_visible_cells())

    def get_hidden_count(self) -> int:
        grid_map = self._get_grid_map()
        if grid_map is None:
            return 0
        return len(grid_map.get_hidden_cells())

    def get_active_source_count(self) -> int:
        with self._lock:
            return len(self._source_cells)
