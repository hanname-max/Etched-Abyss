"""
建造管理器实现

BuildManager 负责处理防御塔的建造逻辑，是战斗系统部署阶段的核心组件。

============================================================================
【架构规范强制声明】
============================================================================

BuildManager 应该通过 ServiceLocator 获取，而不是直接实例化。
它依赖以下服务（必须预先注册到 ServiceLocator）：
- IDataLoader: 用于加载防御塔配置
- EntityManager: 用于创建实体
- GridMap: 用于检查和占用网格
- IGameLogger: 用于记录建造日志

正确示例：
    from CoreLogic import get_service, register_service, BuildManager, GridMap
    
    # 注册依赖服务
    register_service(IDataLoader, MockDataLoader())
    register_service(EntityManager, EntityManager())
    register_service(GridMap, GridMap(width=10, height=10))
    register_service(IGameLogger, GameLogger())
    
    # 注册 BuildManager
    register_service(BuildManager, BuildManager())
    
    # 使用
    build_manager = get_service(BuildManager)
    tower_entity = build_manager.build_tower("tower_arrow_001", 5, 3)

错误示例（严禁使用）：
    # 直接实例化（无法获取依赖服务）
    build_manager = BuildManager()
    tower = build_manager.build_tower("tower_arrow_001", 5, 3)  # 会失败
============================================================================
"""

from typing import Optional
from threading import Lock

from CoreLogic.Interfaces.IDataLoader import IDataLoader
from CoreLogic.Interfaces.IGameLogger import IGameLogger
from CoreLogic.Managers.EntityManager import EntityManager
from CoreLogic.SpaceMapping.GridMap import GridMap
from CoreLogic.DTOs.TowerConfigDTO import TowerConfigDTO
from CoreLogic.Components.TransformComponent import TransformComponent
from CoreLogic.Components.TowerComponent import TowerComponent
from CoreLogic.Core.ServiceLocator import get_service, try_get_service
from CoreLogic.Interfaces.IEntity import IEntity


class BuildManager:
    """
    建造管理器。
    
    负责处理防御塔的建造逻辑，包括网格检查、实体创建和组件挂载。
    
    核心功能：
    1. 检查目标网格是否可通行
    2. 占用网格（设置为不可通行）
    3. 创建防御塔实体并挂载必要组件
    4. 记录详细的建造日志
    
    使用示例：
        build_manager = get_service(BuildManager)
        
        # 建造防御塔
        tower = build_manager.build_tower("tower_arrow_001", 5, 3)
        if tower:
            print(f"建造成功: {tower.entity_id}")
        else:
            print("建造失败")
    """

    def __init__(self):
        """
        初始化建造管理器。
        
        注意：依赖服务通过 ServiceLocator 懒加载获取，
        不应该在构造函数中直接获取，以避免循环依赖问题。
        """
        self._lock: Lock = Lock()
        self._data_loader: Optional[IDataLoader] = None
        self._entity_manager: Optional[EntityManager] = None
        self._grid_map: Optional[GridMap] = None
        self._logger: Optional[IGameLogger] = None

    def _get_data_loader(self) -> IDataLoader:
        """
        获取数据加载器服务。
        
        采用懒加载模式，首次调用时从 ServiceLocator 获取。
        
        返回：
            IDataLoader 实例
            
        异常：
            KeyError: 如果 IDataLoader 未注册到 ServiceLocator
        """
        if self._data_loader is None:
            self._data_loader = get_service(IDataLoader)
        return self._data_loader

    def _get_entity_manager(self) -> EntityManager:
        """
        获取实体管理器服务。
        
        返回：
            EntityManager 实例
            
        异常：
            KeyError: 如果 EntityManager 未注册到 ServiceLocator
        """
        if self._entity_manager is None:
            self._entity_manager = get_service(EntityManager)
        return self._entity_manager

    def _get_grid_map(self) -> GridMap:
        """
        获取网格地图服务。
        
        返回：
            GridMap 实例
            
        异常：
            KeyError: 如果 GridMap 未注册到 ServiceLocator
        """
        if self._grid_map is None:
            self._grid_map = get_service(GridMap)
        return self._grid_map

    def _get_logger(self) -> Optional[IGameLogger]:
        """
        获取日志服务。

        返回：
            IGameLogger 实例，如果未注册则返回 None
        """
        if self._logger is None:
            self._logger = try_get_service(IGameLogger)
        return self._logger

    def build_tower(self, tower_config_id: str, grid_x: int, grid_y: int) -> Optional[IEntity]:
        """
        在指定网格位置建造防御塔。
        
        这是建造系统的核心接口，执行以下步骤：
        1. 检查坐标是否在网格范围内
        2. 检查网格是否可通行（IsWalkable == True）
        3. 如果可通行，将网格设置为不可通行（占位）
        4. 加载防御塔配置
        5. 创建实体并挂载 TransformComponent 和 TowerComponent
        6. 记录详细的建造日志
        
        参数：
            tower_config_id: 防御塔配置的唯一标识符（对应 TowerConfigDTO.id）
            grid_x: 目标网格的 X 坐标
            grid_y: 目标网格的 Y 坐标
            
        返回：
            建造成功返回创建的防御塔实体（IEntity），失败返回 None
            
        可能的失败原因：
            - 坐标越界
            - 网格已被占用（is_walkable == False）
            - 防御塔配置不存在
            - 依赖服务未注册
            
        线程安全：此方法是线程安全的
        """
        with self._lock:
            try:
                logger = self._get_logger()
                grid_map = self._get_grid_map()

                if logger is not None:
                    logger.combat(
                        "开始建造防御塔",
                        tower_config_id=tower_config_id,
                        grid_x=grid_x,
                        grid_y=grid_y
                    )

                if not grid_map.is_valid_position(grid_x, grid_y):
                    if logger is not None:
                        logger.warn(
                            "建造失败：坐标越界",
                            tower_config_id=tower_config_id,
                            grid_x=grid_x,
                            grid_y=grid_y,
                            grid_width=grid_map.width,
                            grid_height=grid_map.height
                        )
                    return None

                is_walkable = grid_map.is_walkable(grid_x, grid_y)

                if is_walkable is None:
                    if logger is not None:
                        logger.error(
                            "建造失败：无法获取网格状态",
                            tower_config_id=tower_config_id,
                            grid_x=grid_x,
                            grid_y=grid_y
                        )
                    return None

                if not is_walkable:
                    if logger is not None:
                        logger.warn(
                            "建造失败：网格已被占用",
                            tower_config_id=tower_config_id,
                            grid_x=grid_x,
                            grid_y=grid_y
                        )
                    return None

                data_loader = self._get_data_loader()
                tower_config = data_loader.load_tower_config(tower_config_id)

                if tower_config is None:
                    if logger is not None:
                        logger.warn(
                            "建造失败：防御塔配置不存在",
                            tower_config_id=tower_config_id,
                            grid_x=grid_x,
                            grid_y=grid_y
                        )
                    return None

                set_success = grid_map.set_walkable(grid_x, grid_y, False)
                if not set_success:
                    if logger is not None:
                        logger.error(
                            "建造失败：无法占用网格",
                            tower_config_id=tower_config_id,
                            grid_x=grid_x,
                            grid_y=grid_y
                        )
                    return None

                if logger is not None:
                    logger.combat(
                        "网格已占用",
                        tower_config_id=tower_config_id,
                        grid_x=grid_x,
                        grid_y=grid_y,
                        tower_name=tower_config.name
                    )

                entity_manager = self._get_entity_manager()
                tower_entity = entity_manager.create_entity()

                transform = TransformComponent(x=float(grid_x), y=float(grid_y))
                tower_entity.add_component(transform)

                tower_component = self._create_tower_component(tower_config)
                tower_entity.add_component(tower_component)

                if logger is not None:
                    logger.combat(
                        "防御塔建造成功",
                        tower_config_id=tower_config_id,
                        tower_name=tower_config.name,
                        entity_id=tower_entity.entity_id,
                        grid_x=grid_x,
                        grid_y=grid_y,
                        damage=tower_config.damage,
                        attack_range=tower_config.attack_range,
                        attack_speed=tower_config.attack_speed,
                        cost=tower_config.cost
                    )

                return tower_entity
                
            except Exception as e:
                try:
                    logger = self._get_logger()
                    if logger is not None:
                        logger.error(
                            "建造过程中发生异常",
                            tower_config_id=tower_config_id,
                            grid_x=grid_x,
                            grid_y=grid_y,
                            exception=e
                        )
                except Exception:
                    pass
                return None

    def _create_tower_component(self, config: TowerConfigDTO) -> TowerComponent:
        """
        从 TowerConfigDTO 创建 TowerComponent。
        
        参数：
            config: 防御塔配置 DTO
            
        返回：
            填充了配置数据的 TowerComponent 实例
        """
        return TowerComponent(
            config_id=config.id,
            name=config.name,
            cost=config.cost,
            damage=config.damage,
            attack_range=config.attack_range,
            attack_speed=config.attack_speed,
            description=config.description,
            upgrade_ids=config.upgrade_ids.copy() if config.upgrade_ids else []
        )

    def can_build(self, grid_x: int, grid_y: int) -> bool:
        """
        检查指定位置是否可以建造防御塔。
        
        用于 UI 层预览或预检查，不实际占用网格。
        
        参数：
            grid_x: 目标网格的 X 坐标
            grid_y: 目标网格的 Y 坐标
            
        返回：
            True 如果可以建造；False 否则
        """
        try:
            grid_map = self._get_grid_map()
            
            if not grid_map.is_valid_position(grid_x, grid_y):
                return False
            
            is_walkable = grid_map.is_walkable(grid_x, grid_y)
            return is_walkable is not None and is_walkable
            
        except Exception:
            return False

    def cancel_build(self, grid_x: int, grid_y: int) -> bool:
        """
        取消建造（释放网格）。
        
        用于撤销建造操作，将网格恢复为可通行状态。
        
        参数：
            grid_x: 目标网格的 X 坐标
            grid_y: 目标网格的 Y 坐标
            
        返回：
            True 如果成功释放网格；False 否则
        """
        with self._lock:
            try:
                grid_map = self._get_grid_map()
                logger = self._get_logger()
                
                if not grid_map.is_valid_position(grid_x, grid_y):
                    return False
                
                success = grid_map.set_walkable(grid_x, grid_y, True)
                
                if success and logger is not None:
                    logger.combat(
                        "已释放网格",
                        grid_x=grid_x,
                        grid_y=grid_y
                    )
                
                return success
                
            except Exception:
                return False
