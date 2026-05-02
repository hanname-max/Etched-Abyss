"""
波次管理器实现

WaveManager 负责根据配置在地图上生成敌人，并为其挂载必要的组件。
它通过 IoC 容器获取依赖，实现了 ITickable 接口以支持波次时间调度。

============================================================================
【架构规范强制声明】
============================================================================

WaveManager 应该通过 ServiceLocator 获取，而不是直接实例化。
它实现了 ITickable 接口，应该注册到 GameLoopManager 以获得每帧更新。

正确示例：
    from CoreLogic import get_service, register_service, WaveManager, GameLoopManager
    
    # 注册到 IoC 容器
    wave_manager = WaveManager()
    register_service(WaveManager, wave_manager)
    
    # 注册到 GameLoopManager 以获得更新
    loop_manager = get_service(GameLoopManager)
    loop_manager.register_tickable(wave_manager)
    
    # 设置起点和终点
    wave_manager.set_spawn_point(0, 0)
    wave_manager.set_end_point(9, 9)
    
    # 开始波次
    wave_manager.start_wave("wave_01_001")

错误示例（严禁使用）：
    # 直接实例化多个 WaveManager
    wm1 = WaveManager()
    wm2 = WaveManager()  # 这会导致状态冲突
============================================================================
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List, Optional, Tuple

from CoreLogic.Core.ServiceLocator import get_service, try_get_service
from CoreLogic.Interfaces.ITickable import ITickable
from CoreLogic.Interfaces.IDataLoader import IDataLoader
from CoreLogic.Interfaces.IGameLogger import IGameLogger
from CoreLogic.Managers.EntityManager import EntityManager
from CoreLogic.SpaceMapping.Pathfinder import Pathfinder
from CoreLogic.SpaceMapping.GridMap import GridMap
from CoreLogic.Components.HealthComponent import HealthComponent
from CoreLogic.Components.TransformComponent import TransformComponent
from CoreLogic.Components.MovementComponent import MovementComponent
from CoreLogic.DTOs.WaveConfigDTO import WaveConfigDTO, EnemySpawnConfig
from CoreLogic.DTOs.EnemyConfigDTO import EnemyConfigDTO


@dataclass
class SpawnTask:
    """
    敌人生成任务。
    
    用于存储待生成敌人的配置和时间信息。
    
    属性：
        enemy_id: 敌人配置的 ID
        spawn_time: 相对于波次开始的生成时间（秒）
        count: 剩余需要生成的数量
        spawn_interval: 同批次敌人之间的生成间隔（秒）
        last_spawn_time: 上一次生成的时间（用于间隔控制）
    """
    enemy_id: str
    spawn_time: float
    count: int
    spawn_interval: float
    last_spawn_time: float = -1.0


class WaveManager(ITickable):
    """
    波次管理器。
    
    负责根据波次配置在地图上生成敌人，为敌人挂载必要的组件，
    并使用 Pathfinder 计算从起点到终点的路径。
    
    核心功能：
    1. 通过 IoC 容器获取依赖（EntityManager, IDataLoader, Pathfinder, GridMap）
    2. 读取 EnemyConfigDTO，创建敌人实体
    3. 为敌人挂载 HealthComponent、TransformComponent、MovementComponent
    4. 生成瞬间调用 Pathfinder 计算路径并赋值给 MovementComponent
    5. 实现 ITickable 接口，支持波次时间调度
    
    使用示例：
        # 获取或创建 WaveManager
        wave_manager = WaveManager()
        register_service(WaveManager, wave_manager)
        
        # 设置必要的依赖（如果未通过 IoC 注册）
        wave_manager.set_grid_map(grid_map)
        wave_manager.set_spawn_point(0, 5)
        wave_manager.set_end_point(9, 5)
        
        # 注册到 GameLoopManager
        loop_manager = get_service(GameLoopManager)
        loop_manager.register_tickable(wave_manager)
        
        # 开始波次
        wave_manager.start_wave("wave_01_001")
        
        # 游戏主循环中会自动生成敌人
        while game_running:
            loop_manager.tick(delta)
    """

    def __init__(self):
        """
        初始化波次管理器。
        """
        self._entity_manager: Optional[EntityManager] = None
        self._data_loader: Optional[IDataLoader] = None
        self._pathfinder: Optional[Pathfinder] = None
        self._grid_map: Optional[GridMap] = None
        self._logger: Optional[IGameLogger] = None
        
        self._spawn_point: Tuple[int, int] = (0, 0)
        self._end_point: Tuple[int, int] = (0, 0)
        
        self._is_running: bool = False
        self._current_wave_id: Optional[str] = None
        self._current_wave_config: Optional[WaveConfigDTO] = None
        self._elapsed_time: float = 0.0
        self._spawn_tasks: Deque[SpawnTask] = deque()
        self._spawned_count: int = 0
        self._total_to_spawn: int = 0

    def _get_entity_manager(self) -> EntityManager:
        """
        获取实体管理器。
        
        优先使用通过 set_entity_manager 设置的实例，
        其次从 ServiceLocator 获取。
        
        返回：
            EntityManager 实例
            
        异常：
            KeyError: 如果 EntityManager 未注册
        """
        if self._entity_manager is not None:
            return self._entity_manager
        return get_service(EntityManager)

    def _get_data_loader(self) -> IDataLoader:
        """
        获取数据加载器。
        
        优先使用通过 set_data_loader 设置的实例，
        其次从 ServiceLocator 获取。
        
        返回：
            IDataLoader 实例
            
        异常：
            KeyError: 如果 IDataLoader 未注册
        """
        if self._data_loader is not None:
            return self._data_loader
        return get_service(IDataLoader)

    def _get_pathfinder(self) -> Pathfinder:
        """
        获取寻路器。
        
        优先使用通过 set_pathfinder 设置的实例，
        其次从 ServiceLocator 获取，
        最后创建新实例。
        
        返回：
            Pathfinder 实例
        """
        if self._pathfinder is not None:
            return self._pathfinder
        pf = try_get_service(Pathfinder)
        if pf is not None:
            return pf
        return Pathfinder()

    def _get_grid_map(self) -> Optional[GridMap]:
        """
        获取网格地图。
        
        返回：
            GridMap 实例，如果未设置则返回 None
        """
        if self._grid_map is not None:
            return self._grid_map
        return try_get_service(GridMap)

    def _get_logger(self) -> Optional[IGameLogger]:
        """
        获取日志记录器。
        
        返回：
            IGameLogger 实例，如果未注册则返回 None
        """
        if self._logger is not None:
            return self._logger
        return try_get_service(IGameLogger)

    def set_entity_manager(self, entity_manager: EntityManager) -> None:
        """
        设置实体管理器。
        
        如果不通过 IoC 容器获取，可以使用此方法手动设置。
        
        参数：
            entity_manager: EntityManager 实例
        """
        self._entity_manager = entity_manager

    def set_data_loader(self, data_loader: IDataLoader) -> None:
        """
        设置数据加载器。
        
        如果不通过 IoC 容器获取，可以使用此方法手动设置。
        
        参数：
            data_loader: IDataLoader 实例
        """
        self._data_loader = data_loader

    def set_pathfinder(self, pathfinder: Pathfinder) -> None:
        """
        设置寻路器。
        
        如果不通过 IoC 容器获取，可以使用此方法手动设置。
        
        参数：
            pathfinder: Pathfinder 实例
        """
        self._pathfinder = pathfinder

    def set_grid_map(self, grid_map: GridMap) -> None:
        """
        设置网格地图。
        
        网格地图用于寻路计算。
        
        参数：
            grid_map: GridMap 实例
        """
        self._grid_map = grid_map

    def set_spawn_point(self, x: int, y: int) -> None:
        """
        设置敌人生成点坐标。
        
        参数：
            x: 生成点的 X 坐标
            y: 生成点的 Y 坐标
        """
        self._spawn_point = (x, y)

    def set_end_point(self, x: int, y: int) -> None:
        """
        设置终点坐标（灯塔位置）。
        
        参数：
            x: 终点的 X 坐标
            y: 终点的 Y 坐标
        """
        self._end_point = (x, y)

    @property
    def spawn_point(self) -> Tuple[int, int]:
        """获取生成点坐标。"""
        return self._spawn_point

    @property
    def end_point(self) -> Tuple[int, int]:
        """获取终点坐标。"""
        return self._end_point

    @property
    def is_running(self) -> bool:
        """波次是否正在运行。"""
        return self._is_running

    @property
    def current_wave_id(self) -> Optional[str]:
        """当前波次的 ID。"""
        return self._current_wave_id

    @property
    def spawned_count(self) -> int:
        """已生成的敌人数量。"""
        return self._spawned_count

    @property
    def total_to_spawn(self) -> int:
        """当前波次总共需要生成的敌人数量。"""
        return self._total_to_spawn

    def start_wave(self, wave_id: str) -> bool:
        """
        开始一个波次。
        
        加载波次配置，准备生成任务队列。
        
        参数：
            wave_id: 波次配置的 ID
            
        返回：
            True 如果波次成功启动；False 如果配置不存在
        """
        if self._is_running:
            self._log_warning(f"WaveManager: Cannot start wave {wave_id}, another wave is already running")
            return False
        
        data_loader = self._get_data_loader()
        wave_config = data_loader.load_wave_config(wave_id)
        
        if wave_config is None:
            self._log_error(f"WaveManager: Wave config not found for id: {wave_id}")
            return False
        
        self._current_wave_id = wave_id
        self._current_wave_config = wave_config
        self._elapsed_time = 0.0
        self._spawned_count = 0
        self._total_to_spawn = sum(s.count for s in wave_config.enemy_spawns)
        self._spawn_tasks = self._create_spawn_tasks(wave_config)
        self._is_running = True
        
        self._log_info(f"WaveManager: Started wave {wave_id}, total enemies: {self._total_to_spawn}")
        return True

    def _create_spawn_tasks(self, wave_config: WaveConfigDTO) -> Deque[SpawnTask]:
        """
        从波次配置创建生成任务队列。
        
        参数：
            wave_config: 波次配置
            
        返回：
            生成任务队列，按 spawn_time 排序
        """
        tasks: List[SpawnTask] = []
        accumulated_time: float = 0.0
        
        for spawn_config in wave_config.enemy_spawns:
            spawn_time = accumulated_time + spawn_config.delay_before
            tasks.append(SpawnTask(
                enemy_id=spawn_config.enemy_id,
                spawn_time=spawn_time,
                count=spawn_config.count,
                spawn_interval=spawn_config.spawn_interval,
                last_spawn_time=-1.0
            ))
            accumulated_time = spawn_time + (spawn_config.count - 1) * spawn_config.spawn_interval
        
        tasks.sort(key=lambda t: t.spawn_time)
        return deque(tasks)

    def stop_wave(self) -> None:
        """
        停止当前波次。
        
        清空生成任务队列，标记波次为已停止。
        """
        if not self._is_running:
            return
        
        self._is_running = False
        self._spawn_tasks.clear()
        self._log_info(f"WaveManager: Stopped wave {self._current_wave_id}")
        self._current_wave_id = None
        self._current_wave_config = None

    def tick(self, delta: float) -> None:
        """
        每帧更新方法，实现 ITickable 接口。
        
        由 GameLoopManager 自动调用，处理敌人的时间调度生成。
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
        """
        if not self._is_running:
            return
        
        if delta < 0:
            delta = 0.0
        
        self._elapsed_time += delta
        self._process_spawn_tasks()
        
        if self._is_wave_complete():
            self._on_wave_complete()

    def _process_spawn_tasks(self) -> None:
        """
        处理生成任务队列。
        
        检查是否有需要生成的敌人，并调用 spawn_enemy 生成。
        """
        while self._spawn_tasks:
            task = self._spawn_tasks[0]
            
            if self._elapsed_time < task.spawn_time:
                break
            
            if task.last_spawn_time < 0:
                self._spawn_enemy(task.enemy_id)
                task.last_spawn_time = self._elapsed_time
                task.count -= 1
                self._spawned_count += 1
            else:
                time_since_last_spawn = self._elapsed_time - task.last_spawn_time
                if time_since_last_spawn >= task.spawn_interval:
                    self._spawn_enemy(task.enemy_id)
                    task.last_spawn_time = self._elapsed_time
                    task.count -= 1
                    self._spawned_count += 1
            
            if task.count <= 0:
                self._spawn_tasks.popleft()
            else:
                break

    def _is_wave_complete(self) -> bool:
        """
        检查波次是否已完成。
        
        返回：
            True 如果所有敌人都已生成
        """
        return self._is_running and len(self._spawn_tasks) == 0

    def _on_wave_complete(self) -> None:
        """
        波次完成回调。
        
        停止波次并记录日志。
        """
        wave_id = self._current_wave_id
        self._is_running = False
        self._current_wave_id = None
        self._current_wave_config = None
        self._log_info(f"WaveManager: Wave {wave_id} completed. Spawned {self._spawned_count} enemies.")

    def _spawn_enemy(self, enemy_id: str) -> bool:
        """
        生成单个敌人。
        
        这是核心方法，执行以下操作：
        1. 加载 EnemyConfigDTO
        2. 调用 EntityManager.create_entity() 创建实体
        3. 添加 HealthComponent（使用配置中的 max_hp）
        4. 添加 TransformComponent（设置为生成点坐标）
        5. 使用 Pathfinder 计算从生成点到终点的路径
        6. 添加 MovementComponent，赋值路径和速度
        
        参数：
            enemy_id: 敌人配置的 ID
            
        返回：
            True 如果敌人成功生成；False 否则
        """
        data_loader = self._get_data_loader()
        enemy_config = data_loader.load_enemy_config(enemy_id)
        
        if enemy_config is None:
            self._log_error(f"WaveManager: Enemy config not found for id: {enemy_id}")
            return False
        
        grid_map = self._get_grid_map()
        if grid_map is None:
            self._log_error("WaveManager: GridMap is not set, cannot spawn enemy")
            return False
        
        path = self._calculate_path(grid_map)
        if not path:
            self._log_warning(
                f"WaveManager: No path found from {self._spawn_point} to {self._end_point}, enemy may not move"
            )
        
        return self._create_enemy_entity(enemy_config, path)

    def _calculate_path(self, grid_map: GridMap) -> List[Tuple[float, float]]:
        """
        计算从生成点到终点的路径。
        
        参数：
            grid_map: 网格地图实例
            
        返回：
            路径点列表（转换为浮点数坐标），如果找不到路径返回空列表
        """
        pathfinder = self._get_pathfinder()
        start_x, start_y = self._spawn_point
        end_x, end_y = self._end_point
        
        path = pathfinder.find_path(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            grid_map=grid_map
        )
        
        return [(float(x), float(y)) for x, y in path]

    def _prepare_waypoints(
        self, 
        path: List[Tuple[float, float]], 
        transform: TransformComponent
    ) -> List[Tuple[float, float]]:
        """
        准备路径点供 MovementComponent 使用。
        
        Pathfinder 返回的路径包含起点，但 MovementComponent 期望
        路径点是"要去的地方"而不是"当前位置"。
        
        如果路径的第一个点与当前位置相同（在极小容差范围内），
        则移除它，这样敌人会直接向下一个点移动。
        
        参数：
            path: 原始路径点列表（从 Pathfinder 返回）
            transform: 敌人的 TransformComponent（包含当前位置）
            
        返回：
            处理后的路径点列表
        """
        if not path:
            return []
        
        epsilon = 0.01
        first_x, first_y = path[0]
        
        dx = first_x - transform.x
        dy = first_y - transform.y
        distance_squared = dx * dx + dy * dy
        
        if distance_squared < epsilon * epsilon:
            return path[1:]
        
        return path

    def _create_enemy_entity(
        self, 
        enemy_config: EnemyConfigDTO, 
        path: List[Tuple[float, float]]
    ) -> bool:
        """
        创建敌人实体并添加所有必要的组件。
        
        参数：
            enemy_config: 敌人配置
            path: 路径点列表
            
        返回：
            True 如果成功创建
        """
        entity_manager = self._get_entity_manager()
        
        entity = entity_manager.create_entity()
        
        transform = TransformComponent(
            x=float(self._spawn_point[0]),
            y=float(self._spawn_point[1])
        )
        entity.add_component(transform)
        
        health = HealthComponent(
            current_health=float(enemy_config.max_hp),
            max_health=float(enemy_config.max_hp)
        )
        entity.add_component(health)
        
        waypoints = self._prepare_waypoints(path, transform)
        
        movement = MovementComponent(
            speed=enemy_config.speed,
            waypoints=waypoints,
            transform=transform
        )
        entity.add_component(movement)
        
        self._log_debug(
            f"WaveManager: Spawned enemy {enemy_config.id} at {self._spawn_point}, "
            f"path length: {len(path)}, speed: {enemy_config.speed}"
        )
        
        return True

    def spawn_enemy_at(self, enemy_id: str, x: int, y: int) -> bool:
        """
        在指定坐标手动生成敌人。
        
        此方法用于调试或特殊情况，不依赖波次配置。
        
        参数：
            enemy_id: 敌人配置的 ID
            x: 生成 X 坐标
            y: 生成 Y 坐标
            
        返回：
            True 如果敌人成功生成
        """
        original_spawn = self._spawn_point
        self._spawn_point = (x, y)
        
        try:
            return self._spawn_enemy(enemy_id)
        finally:
            self._spawn_point = original_spawn

    def reset(self) -> None:
        """
        重置波次管理器状态。
        
        停止当前波次，清除所有状态。
        """
        if self._is_running:
            self.stop_wave()
        
        self._spawn_point = (0, 0)
        self._end_point = (0, 0)
        self._spawned_count = 0
        self._total_to_spawn = 0
        self._elapsed_time = 0.0

    def _log_info(self, message: str) -> None:
        """记录信息日志。"""
        logger = self._get_logger()
        if logger is not None:
            logger.info(message)

    def _log_warning(self, message: str) -> None:
        """记录警告日志。"""
        logger = self._get_logger()
        if logger is not None:
            logger.warn(message)

    def _log_error(self, message: str) -> None:
        """记录错误日志。"""
        logger = self._get_logger()
        if logger is not None:
            logger.error(message)

    def _log_debug(self, message: str) -> None:
        """记录调试日志。"""
        logger = self._get_logger()
        if logger is not None:
            logger.info(message)
