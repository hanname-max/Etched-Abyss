"""
攻城状态系统

SiegeSystem 负责处理敌人在攻城状态下的行为逻辑。
当敌人路径被彻底堵死时，进入攻城状态，开始攻击阻挡它的防御塔。

============================================================================
【架构规范强制声明】
============================================================================

这是一个 System，负责实现业务逻辑：
- 查询拥有 SiegeComponent 的 Entity
- 处理敌人向防御塔移动的逻辑
- 处理周期性攻击防御塔的逻辑
- 处理塔被摧毁后的重寻路逻辑

Component 只是数据容器：
- SiegeComponent: 记录攻城状态数据
- MovementComponent: 控制移动
- TransformComponent: 记录位置
- HealthComponent: 记录生命值（用于攻击塔）
============================================================================
"""

from typing import Optional, Tuple, List
from collections import deque

from CoreLogic.Interfaces.ITickable import ITickable
from CoreLogic.Components.SiegeComponent import SiegeComponent
from CoreLogic.Components.MovementComponent import MovementComponent
from CoreLogic.Components.TransformComponent import TransformComponent
from CoreLogic.Components.HealthComponent import HealthComponent
from CoreLogic.Components.TowerComponent import TowerComponent
from CoreLogic.SpaceMapping.GridMap import GridMap
from CoreLogic.SpaceMapping.Pathfinder import Pathfinder
from CoreLogic.Systems.HealthSystem import HealthSystem
from CoreLogic.Managers.EntityManager import EntityManager
from CoreLogic.Core.ServiceLocator import try_get_service, get_service
from CoreLogic.Interfaces.IGameLogger import IGameLogger


class SiegeSystem(ITickable):
    """
    攻城状态系统。
    
    负责处理敌人在攻城状态下的行为逻辑：
    1. 每帧更新攻城状态的敌人
    2. 检查目标塔是否还存在
    3. 向塔移动并在相邻格子停止
    4. 周期性攻击塔
    5. 塔被摧毁后触发重寻路
    
    使用示例：
        # 初始化攻城系统
        siege_system = SiegeSystem()
        siege_system.initialize()
        
        # 注册到 GameLoopManager 以获得每帧更新
        from CoreLogic import GameLoopManager, get_service
        loop_manager = get_service(GameLoopManager)
        loop_manager.register_tickable(siege_system)
        
        # 此时敌人会自动：
        # - 向目标塔移动
        # - 在相邻格子时攻击塔
        # - 塔被摧毁后重寻路
        
        # 关闭时停止
        siege_system.shutdown()
    """
    
    _DIRECTIONS: List[Tuple[int, int]] = [
        (0, -1),
        (0, 1),
        (-1, 0),
        (1, 0),
    ]
    
    def __init__(self) -> None:
        """
        初始化攻城系统。
        
        注意：这只是创建实例，需要手动调用 initialize()，
        并注册到 GameLoopManager 以获得每帧更新。
        """
        self._is_initialized: bool = False
        self._pathfinder: Optional[Pathfinder] = None
        self._health_system: Optional[HealthSystem] = None
    
    def initialize(self) -> None:
        """
        初始化攻城系统。
        """
        if self._is_initialized:
            return
        
        self._is_initialized = True
    
    def shutdown(self) -> None:
        """
        关闭攻城系统。
        """
        if not self._is_initialized:
            return
        
        self._is_initialized = False
    
    def is_initialized(self) -> bool:
        """
        检查攻城系统是否已初始化。
        
        返回：
            True 如果已初始化；否则返回 False
        """
        return self._is_initialized
    
    def _get_entity_manager(self) -> Optional[EntityManager]:
        """
        从 ServiceLocator 获取 EntityManager。
        
        返回：
            EntityManager 实例，如果未注册则返回 None
        """
        return try_get_service(EntityManager)
    
    def _get_grid_map(self) -> Optional[GridMap]:
        """
        从 ServiceLocator 获取 GridMap。
        
        返回：
            GridMap 实例，如果未注册则返回 None
        """
        return try_get_service(GridMap)
    
    def _get_pathfinder(self) -> Pathfinder:
        """
        获取寻路器实例。
        
        返回：
            Pathfinder 实例
        """
        if self._pathfinder is not None:
            return self._pathfinder
        
        pf = try_get_service(Pathfinder)
        if pf is not None:
            self._pathfinder = pf
            return pf
        
        self._pathfinder = Pathfinder()
        return self._pathfinder
    
    def _get_health_system(self) -> HealthSystem:
        """
        获取健康系统实例。
        
        返回：
            HealthSystem 实例
        """
        if self._health_system is not None:
            return self._health_system
        
        hs = try_get_service(HealthSystem)
        if hs is not None:
            self._health_system = hs
            return hs
        
        self._health_system = HealthSystem()
        return self._health_system
    
    def _get_logger(self) -> Optional[IGameLogger]:
        """
        从 ServiceLocator 获取日志器。
        
        返回：
            如果已注册，返回 IGameLogger 实例；否则返回 None
        """
        return try_get_service(IGameLogger)
    
    def _log_siege(self, message: str, **kwargs) -> None:
        """
        记录攻城相关日志。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数
        """
        logger = self._get_logger()
        if logger is not None:
            logger.info(message, **kwargs)
    
    def tick(self, delta: float) -> None:
        """
        每帧更新方法，实现 ITickable 接口。
        
        由 GameLoopManager 每帧调用。
        
        更新逻辑：
        1. 从 ServiceLocator 获取 EntityManager
        2. 查询所有拥有 SiegeComponent 的实体
        3. 对每个处于攻城状态的敌人：
           a. 检查目标塔是否还存在且存活
           b. 如果塔已被摧毁，触发重寻路
           c. 否则，向塔移动并攻击
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
        """
        if delta < 0:
            delta = 0.0
        
        entity_manager = self._get_entity_manager()
        if entity_manager is None:
            return
        
        grid_map = self._get_grid_map()
        
        entities = entity_manager.get_entities_with_component(SiegeComponent)
        
        for entity in entities:
            siege_comp = entity.get_component(SiegeComponent)
            if siege_comp is None:
                continue
            
            if not siege_comp.is_active:
                continue
            
            self._process_siege_entity(entity, siege_comp, entity_manager, grid_map, delta)
    
    def _process_siege_entity(
        self,
        enemy,
        siege_comp: SiegeComponent,
        entity_manager: EntityManager,
        grid_map: Optional[GridMap],
        delta: float,
    ) -> None:
        """
        处理单个攻城状态的敌人。
        
        参数：
            enemy: 敌人实体
            siege_comp: SiegeComponent 实例
            entity_manager: EntityManager 实例
            grid_map: GridMap 实例（可选）
            delta: 帧时间
        """
        target_tower = self._get_target_tower(siege_comp, entity_manager)
        
        if target_tower is None:
            self._on_tower_destroyed(enemy, siege_comp, entity_manager, grid_map)
            return
        
        tower_health = target_tower.get_component(HealthComponent)
        if tower_health is None or tower_health.current_health <= 0:
            self._on_tower_destroyed(enemy, siege_comp, entity_manager, grid_map)
            return
        
        enemy_transform = enemy.get_component(TransformComponent)
        if enemy_transform is None:
            return
        
        enemy_grid_x = int(round(enemy_transform.x))
        enemy_grid_y = int(round(enemy_transform.y))
        
        tower_transform = target_tower.get_component(TransformComponent)
        if tower_transform is None:
            return
        
        tower_grid_x = int(round(tower_transform.x))
        tower_grid_y = int(round(tower_transform.y))
        
        is_adjacent = self._is_adjacent(enemy_grid_x, enemy_grid_y, tower_grid_x, tower_grid_y)
        
        if is_adjacent:
            self._attack_tower(enemy, siege_comp, target_tower, delta)
        else:
            self._move_to_tower(enemy, siege_comp, tower_grid_x, tower_grid_y, grid_map)
    
    def _get_target_tower(
        self,
        siege_comp: SiegeComponent,
        entity_manager: EntityManager,
    ):
        """
        获取目标塔实体。
        
        参数：
            siege_comp: SiegeComponent 实例
            entity_manager: EntityManager 实例
            
        返回：
            塔实体如果存在且有 TowerComponent；否则返回 None
        """
        if siege_comp.target_tower_id is None:
            return None
        
        tower = entity_manager.get_entity(siege_comp.target_tower_id)
        if tower is None:
            return None
        
        if not tower.has_component(TowerComponent):
            return None
        
        return tower
    
    def _is_adjacent(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
    ) -> bool:
        """
        检查两个网格坐标是否相邻（上下左右）。
        
        参数：
            x1, y1: 第一个坐标
            x2, y2: 第二个坐标
            
        返回：
            True 如果相邻
        """
        dx = abs(x1 - x2)
        dy = abs(y1 - y2)
        return (dx == 1 and dy == 0) or (dx == 0 and dy == 1)
    
    def _move_to_tower(
        self,
        enemy,
        siege_comp: SiegeComponent,
        tower_grid_x: int,
        tower_grid_y: int,
        grid_map: Optional[GridMap],
    ) -> None:
        """
        让敌人向塔移动。
        
        找到塔附近的相邻可通行格子，让敌人移动过去。
        
        参数：
            enemy: 敌人实体
            siege_comp: SiegeComponent 实例
            tower_grid_x: 塔的 X 网格坐标
            tower_grid_y: 塔的 Y 网格坐标
            grid_map: GridMap 实例（可选）
        """
        movement_comp = enemy.get_component(MovementComponent)
        if movement_comp is None:
            return
        
        if movement_comp.has_waypoints:
            return
        
        enemy_transform = enemy.get_component(TransformComponent)
        if enemy_transform is None:
            return
        
        current_x = int(round(enemy_transform.x))
        current_y = int(round(enemy_transform.y))
        
        if grid_map is None:
            self._move_directly(movement_comp, tower_grid_x, tower_grid_y, current_x, current_y)
            return
        
        target_cell = self._find_adjacent_walkable_cell(
            tower_grid_x, tower_grid_y, grid_map
        )
        
        if target_cell is None:
            self._move_directly(movement_comp, tower_grid_x, tower_grid_y, current_x, current_y)
            return
        
        target_x, target_y = target_cell
        
        pathfinder = self._get_pathfinder()
        path = pathfinder.find_path(
            start_x=current_x,
            start_y=current_y,
            end_x=target_x,
            end_y=target_y,
            grid_map=grid_map
        )
        
        if path:
            prepared_path = self._prepare_waypoints(path, enemy_transform)
            movement_comp.add_waypoints(prepared_path)
        else:
            self._move_directly(movement_comp, target_x, target_y, current_x, current_y)
    
    def _find_adjacent_walkable_cell(
        self,
        tower_x: int,
        tower_y: int,
        grid_map: GridMap,
    ) -> Optional[Tuple[int, int]]:
        """
        找到塔附近的一个可通行格子。
        
        参数：
            tower_x: 塔的 X 坐标
            tower_y: 塔的 Y 坐标
            grid_map: GridMap 实例
            
        返回：
            相邻可通行格子的坐标，如果没有则返回 None
        """
        for dx, dy in self._DIRECTIONS:
            nx = tower_x + dx
            ny = tower_y + dy
            
            is_walkable = grid_map.is_walkable(nx, ny)
            if is_walkable is True:
                return (nx, ny)
        
        return None
    
    def _move_directly(
        self,
        movement_comp: MovementComponent,
        target_x: int,
        target_y: int,
        current_x: int,
        current_y: int,
    ) -> None:
        """
        直接移动到目标位置（用于没有 GridMap 或寻路失败的情况）。
        
        参数：
            movement_comp: MovementComponent 实例
            target_x: 目标 X 坐标
            target_y: 目标 Y 坐标
            current_x: 当前 X 坐标
            current_y: 当前 Y 坐标
        """
        if current_x != target_x or current_y != target_y:
            movement_comp.add_waypoint(float(target_x), float(target_y))
    
    def _prepare_waypoints(
        self,
        path: List[Tuple[int, int]],
        transform: TransformComponent,
    ) -> List[Tuple[float, float]]:
        """
        准备路径点供 MovementComponent 使用。
        
        参数：
            path: 从 Pathfinder 返回的路径点列表（整数坐标）
            transform: 敌人的 TransformComponent
            
        返回：
            处理后的路径点列表（浮点数坐标）
        """
        if not path:
            return []
        
        float_path = [(float(x), float(y)) for x, y in path]
        
        epsilon = 0.01
        first_x, first_y = float_path[0]
        
        dx = first_x - transform.x
        dy = first_y - transform.y
        distance_squared = dx * dx + dy * dy
        
        if distance_squared < epsilon * epsilon:
            return float_path[1:]
        
        return float_path
    
    def _attack_tower(
        self,
        enemy,
        siege_comp: SiegeComponent,
        tower,
        delta: float,
    ) -> None:
        """
        让敌人攻击塔。
        
        参数：
            enemy: 敌人实体
            siege_comp: SiegeComponent 实例
            tower: 目标塔实体
            delta: 帧时间
        """
        siege_comp.update_cooldown(delta)
        
        if not siege_comp.is_ready:
            return
        
        tower_health = tower.get_component(HealthComponent)
        if tower_health is None:
            return
        
        health_system = self._get_health_system()
        
        old_health = tower_health.current_health
        health_system.take_damage(tower, siege_comp.attack_damage)
        new_health = tower_health.current_health
        
        siege_comp.start_cooldown()
        
        self._log_siege(
            "敌人攻击防御塔",
            enemy_id=enemy.entity_id,
            tower_id=tower.entity_id,
            damage_dealt=siege_comp.attack_damage,
            old_health=old_health,
            new_health=new_health,
        )
        
        if new_health <= 0 and old_health > 0:
            self._log_siege(
                "防御塔被摧毁",
                enemy_id=enemy.entity_id,
                tower_id=tower.entity_id,
            )
    
    def _on_tower_destroyed(
        self,
        enemy,
        siege_comp: SiegeComponent,
        entity_manager: EntityManager,
        grid_map: Optional[GridMap],
    ) -> None:
        """
        当塔被摧毁时的处理逻辑。
        
        1. 取消攻城状态
        2. 清除现有路径
        3. 尝试重新寻路到原始终点
        
        参数：
            enemy: 敌人实体
            siege_comp: SiegeComponent 实例
            entity_manager: EntityManager 实例
            grid_map: GridMap 实例（可选）
        """
        tower_id = siege_comp.target_tower_id
        siege_comp.deactivate()
        
        movement_comp = enemy.get_component(MovementComponent)
        if movement_comp is not None:
            movement_comp.clear_waypoints()
        
        enemy_transform = enemy.get_component(TransformComponent)
        if enemy_transform is None:
            return
        
        if grid_map is None:
            self._log_siege(
                "无法重寻路：GridMap 不可用",
                enemy_id=enemy.entity_id,
            )
            return
        
        current_x = int(round(enemy_transform.x))
        current_y = int(round(enemy_transform.y))
        end_x = int(round(siege_comp.destination_x))
        end_y = int(round(siege_comp.destination_y))
        
        self._log_siege(
            "塔被摧毁，敌人尝试重寻路",
            enemy_id=enemy.entity_id,
            tower_id=tower_id,
            start=(current_x, current_y),
            end=(end_x, end_y),
        )
        
        pathfinder = self._get_pathfinder()
        new_path = pathfinder.find_path(
            start_x=current_x,
            start_y=current_y,
            end_x=end_x,
            end_y=end_y,
            grid_map=grid_map
        )
        
        if new_path and movement_comp is not None:
            prepared_path = self._prepare_waypoints(new_path, enemy_transform)
            movement_comp.add_waypoints(prepared_path)
            
            self._log_siege(
                "敌人重寻路成功",
                enemy_id=enemy.entity_id,
                path_length=len(prepared_path),
            )
        else:
            self._log_siege(
                "敌人重寻路失败，仍然被困",
                enemy_id=enemy.entity_id,
            )
            
            self._find_new_target(
                enemy, siege_comp, entity_manager, grid_map,
                current_x, current_y, end_x, end_y
            )
    
    def _find_new_target(
        self,
        enemy,
        siege_comp: SiegeComponent,
        entity_manager: EntityManager,
        grid_map: GridMap,
        current_x: int,
        current_y: int,
        end_x: int,
        end_y: int,
    ) -> None:
        """
        寻找新的目标塔（重寻路失败后）。
        
        参数：
            enemy: 敌人实体
            siege_comp: SiegeComponent 实例
            entity_manager: EntityManager 实例
            grid_map: GridMap 实例
            current_x: 当前 X 坐标
            current_y: 当前 Y 坐标
            end_x: 终点 X 坐标
            end_y: 终点 Y 坐标
        """
        nearest_tower = self._find_nearest_blocking_tower(
            entity_manager, grid_map, current_x, current_y
        )
        
        if nearest_tower is None:
            self._log_siege(
                "无法找到新的目标塔",
                enemy_id=enemy.entity_id,
            )
            return
        
        tower_entity, tower_grid = nearest_tower
        
        enemy_config_damage = siege_comp.attack_damage
        
        siege_comp.activate(
            target_tower_id=tower_entity.entity_id,
            target_tower_grid=tower_grid,
            attack_damage=enemy_config_damage,
            attack_interval=siege_comp.attack_interval,
            destination_x=float(end_x),
            destination_y=float(end_y),
        )
        
        self._log_siege(
            "敌人找到新的目标塔，进入攻城状态",
            enemy_id=enemy.entity_id,
            tower_id=tower_entity.entity_id,
            tower_grid=tower_grid,
        )
    
    def _find_nearest_blocking_tower(
        self,
        entity_manager: EntityManager,
        grid_map: GridMap,
        current_x: int,
        current_y: int,
    ) -> Optional[Tuple]:
        """
        寻找最近的阻挡防御塔。
        
        防御塔定义为：
        1. 拥有 TowerComponent
        2. 所在格子 IsWalkable 为 False
        3. 从当前位置看，是通往终点路径上的阻挡者
        
        参数：
            entity_manager: EntityManager 实例
            grid_map: GridMap 实例
            current_x: 当前 X 坐标
            current_y: 当前 Y 坐标
            
        返回：
            (塔实体, 网格坐标) 元组，如果没有则返回 None
        """
        towers = entity_manager.get_entities_with_component(TowerComponent)
        
        nearest_tower = None
        nearest_distance_squared = float('inf')
        
        for tower in towers:
            tower_transform = tower.get_component(TransformComponent)
            if tower_transform is None:
                continue
            
            tower_health = tower.get_component(HealthComponent)
            if tower_health is None or tower_health.current_health <= 0:
                continue
            
            tower_grid_x = int(round(tower_transform.x))
            tower_grid_y = int(round(tower_transform.y))
            
            is_walkable = grid_map.is_walkable(tower_grid_x, tower_grid_y)
            if is_walkable is not False:
                continue
            
            dx = tower_grid_x - current_x
            dy = tower_grid_y - current_y
            distance_squared = dx * dx + dy * dy
            
            if distance_squared < nearest_distance_squared:
                nearest_distance_squared = distance_squared
                nearest_tower = (tower, (tower_grid_x, tower_grid_y))
        
        return nearest_tower
