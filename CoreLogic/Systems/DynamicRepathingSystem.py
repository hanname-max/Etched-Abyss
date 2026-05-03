"""
动态重寻路系统

DynamicRepathingSystem 负责处理玩家造塔堵路时的敌人路径更新。

============================================================================
【架构规范强制声明】
============================================================================

当新塔建造完成时，BuildManager 会发布 TowerBuiltEvent。
DynamicRepathingSystem 订阅此事件，检查所有存活敌人的路径是否被阻断。

如果路径被阻断：
1. 挂起当前移动（通过清空 waypoints 或重新赋值）
2. 从当前位置重新计算到终点的路径
3. 将新路径赋值给 MovementComponent

设计原则：
- 所有业务逻辑在 System 中实现
- Component 只是纯粹的数据容器
- 跨域通信通过 EventBus 进行
============================================================================
"""

from typing import List, Tuple, Optional
from collections import deque

from CoreLogic.Interfaces.IEntity import IEntity
from CoreLogic.Interfaces.IGameLogger import IGameLogger
from CoreLogic.Core.ServiceLocator import get_service, try_get_service
from CoreLogic.Core.EventBus import subscribe, unsubscribe
from CoreLogic.Events.TowerBuiltEvent import TowerBuiltEvent
from CoreLogic.Managers.EntityManager import EntityManager
from CoreLogic.SpaceMapping.Pathfinder import Pathfinder
from CoreLogic.SpaceMapping.GridMap import GridMap
from CoreLogic.Components.HealthComponent import HealthComponent
from CoreLogic.Components.MovementComponent import MovementComponent
from CoreLogic.Components.TransformComponent import TransformComponent
from CoreLogic.Components.TowerComponent import TowerComponent
from CoreLogic.Components.SiegeComponent import SiegeComponent


class DynamicRepathingSystem:
    """
    动态重寻路系统。
    
    负责在防御塔建造时检查敌人路径是否被阻断，并触发重新寻路。
    
    核心功能：
    1. 订阅 TowerBuiltEvent 事件
    2. 当塔建造时，检查所有存活敌人的路径
    3. 如果路径被阻断，从当前位置重新计算路径
    4. 更新受影响敌人的 MovementComponent
    
    使用示例：
        # 创建并启用动态重寻路系统
        repathing_system = DynamicRepathingSystem()
        repathing_system.enable()
        
        # 当塔建造时，系统会自动处理敌人的重寻路
        
        # 禁用系统
        repathing_system.disable()
    """
    
    def __init__(self) -> None:
        """
        初始化动态重寻路系统。
        """
        self._is_enabled: bool = False
        self._pathfinder: Optional[Pathfinder] = None
    
    def _get_entity_manager(self) -> EntityManager:
        """
        从 ServiceLocator 获取实体管理器。
        
        返回：
            EntityManager 实例
            
        异常：
            KeyError: 如果 EntityManager 未注册
        """
        return get_service(EntityManager)
    
    def _get_grid_map(self) -> Optional[GridMap]:
        """
        从 ServiceLocator 获取网格地图。
        
        返回：
            GridMap 实例，如果未注册则返回 None
        """
        return try_get_service(GridMap)
    
    def _get_pathfinder(self) -> Pathfinder:
        """
        获取寻路器实例。
        
        优先使用已创建的实例，其次从 ServiceLocator 获取，
        最后创建新实例。
        
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
    
    def _get_logger(self) -> Optional[IGameLogger]:
        """
        从 ServiceLocator 获取日志器。
        
        返回：
            IGameLogger 实例，如果未注册则返回 None
        """
        return try_get_service(IGameLogger)
    
    def _log_info(self, message: str, **kwargs) -> None:
        """
        记录信息日志。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数
        """
        logger = self._get_logger()
        if logger is not None:
            logger.info(message, **kwargs)
    
    def _log_warning(self, message: str, **kwargs) -> None:
        """
        记录警告日志。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数
        """
        logger = self._get_logger()
        if logger is not None:
            logger.warn(message, **kwargs)
    
    def enable(self) -> None:
        """
        启用动态重寻路系统。
        
        订阅 TowerBuiltEvent 事件。
        """
        if self._is_enabled:
            return
        
        subscribe(TowerBuiltEvent, self._on_tower_built)
        self._is_enabled = True
        self._log_info("DynamicRepathingSystem: 已启用动态重寻路系统")
    
    def disable(self) -> None:
        """
        禁用动态重寻路系统。
        
        取消订阅 TowerBuiltEvent 事件。
        """
        if not self._is_enabled:
            return
        
        unsubscribe(TowerBuiltEvent, self._on_tower_built)
        self._is_enabled = False
        self._log_info("DynamicRepathingSystem: 已禁用动态重寻路系统")
    
    @property
    def is_enabled(self) -> bool:
        """
        系统是否已启用。
        
        返回：
            True 如果系统已启用；否则返回 False
        """
        return self._is_enabled
    
    def _on_tower_built(self, event: TowerBuiltEvent) -> None:
        """
        塔建造事件处理函数。
        
        当 TowerBuiltEvent 发布时被调用，执行以下操作：
        1. 获取所有存活的敌人实体
        2. 检查每个敌人的路径是否被新建的塔阻断
        3. 如果被阻断，触发重新寻路
        
        参数：
            event: TowerBuiltEvent 事件实例
        """
        self._log_info(
            "DynamicRepathingSystem: 检测到新塔建造",
            tower_entity_id=event.tower_entity_id,
            grid_x=event.grid_x,
            grid_y=event.grid_y,
            tower_config_id=event.tower_config_id
        )
        
        grid_map = self._get_grid_map()
        if grid_map is None:
            self._log_warning("DynamicRepathingSystem: 无法获取 GridMap，跳过重寻路检查")
            return
        
        try:
            entity_manager = self._get_entity_manager()
        except KeyError:
            self._log_warning("DynamicRepathingSystem: 无法获取 EntityManager，跳过重寻路检查")
            return
        
        enemies = self._get_alive_enemies(entity_manager)

        if not enemies:
            self._log_info("DynamicRepathingSystem: 没有存活的敌人，无需检查")
            return

        nearby_enemies = self._filter_nearby_enemies(enemies, event.grid_x, event.grid_y)

        affected_count = 0
        for enemy in nearby_enemies:
            if self._check_and_repath(enemy, event.grid_x, event.grid_y, grid_map):
                affected_count += 1
        
        self._log_info(
            "DynamicRepathingSystem: 重寻路检查完成",
            total_enemies=len(enemies),
            nearby_enemies=len(nearby_enemies),
            affected_enemies=affected_count
        )
    
    def _get_alive_enemies(self, entity_manager: EntityManager) -> List[IEntity]:
        """
        获取所有存活的敌人实体。
        
        存活的敌人定义为：
        1. 拥有 HealthComponent 且 current_health > 0
        2. 拥有 MovementComponent（有路径需要更新）
        3. 拥有 TransformComponent（有当前位置）
        
        参数：
            entity_manager: EntityManager 实例
            
        返回：
            存活敌人实体的列表
        """
        candidates = entity_manager.get_entities_with_component(HealthComponent)
        alive_enemies: List[IEntity] = []
        
        for entity in candidates:
            health = entity.get_component(HealthComponent)
            movement = entity.get_component(MovementComponent)
            transform = entity.get_component(TransformComponent)
            
            if (health is not None and health.current_health > 0 and
                movement is not None and transform is not None):
                alive_enemies.append(entity)
        
        return alive_enemies

    def _filter_nearby_enemies(
        self, enemies: List[IEntity], tower_x: int, tower_y: int, max_range: int = 50
    ) -> List[IEntity]:
        nearby: List[IEntity] = []
        for enemy in enemies:
            movement = enemy.get_component(MovementComponent)
            if movement is None or not movement.waypoints:
                continue
            end_wp = movement.waypoints[-1]
            dist = abs(end_wp[0] - tower_x) + abs(end_wp[1] - tower_y)
            if dist < max_range:
                nearby.append(enemy)
        return nearby

    def _check_and_repath(
        self, 
        enemy: IEntity, 
        tower_grid_x: int, 
        tower_grid_y: int,
        grid_map: GridMap
    ) -> bool:
        """
        检查敌人的路径是否被阻断，如果是则触发重新寻路。
        
        参数：
            enemy: 敌人实体
            tower_grid_x: 新建塔的 X 网格坐标
            tower_grid_y: 新建塔的 Y 网格坐标
            grid_map: 网格地图实例
            
        返回：
            True 如果敌人被影响并重新寻路；否则返回 False
        """
        health = enemy.get_component(HealthComponent)
        if health is None or health.current_health <= 0:
            return False
        
        movement = enemy.get_component(MovementComponent)
        transform = enemy.get_component(TransformComponent)
        
        if movement is None or transform is None:
            return False
        
        if not movement.has_waypoints:
            return False
        
        if self._is_path_blocked(movement.waypoints, tower_grid_x, tower_grid_y):
            self._log_info(
                "DynamicRepathingSystem: 敌人路径被阻断，触发重新寻路",
                entity_id=enemy.entity_id,
                tower_x=tower_grid_x,
                tower_y=tower_grid_y
            )
            return self._repath_enemy(enemy, movement, transform, grid_map)
        
        return False
    
    def _is_path_blocked(
        self,
        waypoints: deque,
        tower_grid_x: int,
        tower_grid_y: int
    ) -> bool:
        prev_x, prev_y = None, None
        for wx, wy in waypoints:
            gx, gy = int(round(wx)), int(round(wy))
            if gx == tower_grid_x and gy == tower_grid_y:
                return True
            if prev_x is not None:
                if self._segment_hits_cell(prev_x, prev_y, gx, gy, tower_grid_x, tower_grid_y):
                    return True
            prev_x, prev_y = gx, gy
        return False

    def _segment_hits_cell(
        self, x0: int, y0: int, x1: int, y1: int, cx: int, cy: int
    ) -> bool:
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        cx_cur, cy_cur = x0, y0
        while True:
            if cx_cur == cx and cy_cur == cy:
                return True
            if cx_cur == x1 and cy_cur == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx_cur += sx
            if e2 < dx:
                err += dx
                cy_cur += sy
        return False
    
    def _repath_enemy(
        self,
        enemy: IEntity,
        movement: MovementComponent,
        transform: TransformComponent,
        grid_map: GridMap
    ) -> bool:
        """
        为敌人重新计算路径。
        
        执行以下操作：
        1. 确定起点：敌人当前位置（四舍五入到最近的网格）
        2. 确定终点：敌人原始终点（从 waypoints 的最后一个点获取）
        3. 调用 Pathfinder.find_path() 计算新路径
        4. 如果找到新路径，更新 MovementComponent 的 waypoints
        
        参数：
            enemy: 敌人实体
            movement: MovementComponent 实例
            transform: TransformComponent 实例
            grid_map: GridMap 实例
            
        返回：
            True 如果成功找到新路径并更新；否则返回 False
        """
        if not movement.waypoints:
            return False
        
        current_x = int(round(transform.x))
        current_y = int(round(transform.y))
        
        last_wp_x, last_wp_y = movement.waypoints[-1]
        end_x = int(round(last_wp_x))
        end_y = int(round(last_wp_y))
        
        self._log_info(
            "DynamicRepathingSystem: 开始重新寻路",
            entity_id=enemy.entity_id,
            start=(current_x, current_y),
            end=(end_x, end_y)
        )
        
        pathfinder = self._get_pathfinder()
        new_path = pathfinder.find_path(
            start_x=current_x,
            start_y=current_y,
            end_x=end_x,
            end_y=end_y,
            grid_map=grid_map
        )
        
        if not new_path:
            self._log_warning(
                "DynamicRepathingSystem: 无法找到新路径，敌人被困住",
                entity_id=enemy.entity_id,
                start=(current_x, current_y),
                end=(end_x, end_y)
            )
            
            self._enter_siege_state(enemy, grid_map, current_x, current_y, end_x, end_y)
            return False
        
        prepared_waypoints = self._prepare_waypoints(new_path, transform)

        old_path_length = len(movement.waypoints)
        movement.clear_waypoints()
        movement.add_waypoints(prepared_waypoints)

        self._log_info(
            "DynamicRepathingSystem: 成功更新敌人路径",
            entity_id=enemy.entity_id,
            old_path_length=old_path_length,
            new_path_length=len(prepared_waypoints)
        )
        
        return True
    
    def _prepare_waypoints(
        self, 
        path: List[Tuple[int, int]], 
        transform: TransformComponent
    ) -> List[Tuple[float, float]]:
        """
        准备路径点供 MovementComponent 使用。
        
        参考 WaveManager._prepare_waypoints 的逻辑：
        - Pathfinder 返回的路径包含起点
        - 如果路径的第一个点与当前位置相同（在极小容差范围内），则移除它
        - 将整数坐标转换为浮点数坐标
        
        参数：
            path: 从 Pathfinder 返回的路径点列表（整数坐标）
            transform: 敌人的 TransformComponent（包含当前位置）
            
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
    
    def _enter_siege_state(
        self,
        enemy: IEntity,
        grid_map: GridMap,
        current_x: int,
        current_y: int,
        end_x: int,
        end_y: int,
    ) -> None:
        """
        让敌人进入攻城状态。
        
        当敌人的路径被彻底堵死（Pathfinder 返回空队列）时调用。
        
        执行以下操作：
        1. 寻找最近的阻挡防御塔
        2. 给敌人添加 SiegeComponent 并激活
        3. 记录攻城状态日志
        
        参数：
            enemy: 敌人实体
            grid_map: GridMap 实例
            current_x: 当前 X 网格坐标
            current_y: 当前 Y 网格坐标
            end_x: 终点 X 网格坐标
            end_y: 终点 Y 网格坐标
        """
        entity_manager = self._get_entity_manager()
        
        nearest_tower = self._find_nearest_blocking_tower(
            entity_manager, grid_map, current_x, current_y
        )
        
        if nearest_tower is None:
            self._log_warning(
                "DynamicRepathingSystem: 无法找到目标防御塔，敌人无法进入攻城状态",
                enemy_id=enemy.entity_id,
            )
            return
        
        tower_entity, tower_grid = nearest_tower
        
        siege_comp = enemy.get_component(SiegeComponent)
        if siege_comp is None:
            siege_comp = SiegeComponent()
            enemy.add_component(siege_comp)
        
        if siege_comp.is_active:
            return
        
        enemy_health = enemy.get_component(HealthComponent)
        attack_interval = 1.0
        # 攻城伤害基于敌人血量的启发式计算，后续应从 EnemyConfigDTO 读取
        attack_damage = max(5.0, enemy_health.max_health / 10.0) if enemy_health and enemy_health.max_health > 0 else 10.0
        
        siege_comp.activate(
            target_tower_id=tower_entity.entity_id,
            target_tower_grid=tower_grid,
            attack_damage=attack_damage,
            attack_interval=attack_interval,
            destination_x=float(end_x),
            destination_y=float(end_y),
        )
        
        self._log_info(
            "DynamicRepathingSystem: 敌人进入攻城状态",
            enemy_id=enemy.entity_id,
            tower_id=tower_entity.entity_id,
            tower_grid=tower_grid,
            attack_damage=attack_damage,
            attack_interval=attack_interval,
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
        3. 有 HealthComponent 且存活
        
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
