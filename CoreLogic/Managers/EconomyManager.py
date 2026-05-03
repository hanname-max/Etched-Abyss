"""
经济管理器

EconomyManager 负责管理游戏中的双轨经济系统之一：灵魂碎片（Souls）。

============================================================================
【架构规范强制声明】
============================================================================

EconomyManager 应该通过 ServiceLocator 获取，而不是直接实例化。
它依赖以下服务（必须预先注册到 ServiceLocator）：
- IDataLoader: 用于加载敌人配置（获取击杀奖励）
- IGameLogger: 用于记录经济日志

此管理器通过 EventBus 订阅 EntityDeathEvent 来获取击杀奖励，
并提供 can_afford 和 try_spend_souls 方法进行经济鉴权。

正确示例：
    from CoreLogic import get_service, register_service, EconomyManager, IGameLogger, GameLogger
    
    # 注册依赖服务
    register_service(IGameLogger, GameLogger())
    register_service(EconomyManager, EconomyManager())
    
    # 使用
    economy_manager = get_service(EconomyManager)
    economy_manager.initialize()  # 开始监听敌人死亡事件
    
    # 检查是否可以建造
    if economy_manager.can_afford(100):
        if economy_manager.try_spend_souls(100):
            print("建造成功！")
============================================================================
"""

from threading import Lock
from typing import Optional

from CoreLogic.Events.EntityDeathEvent import EntityDeathEvent
from CoreLogic.Core.ServiceLocator import get_service, try_get_service
from CoreLogic.Core.EventBus import subscribe, unsubscribe
from CoreLogic.Interfaces.IGameLogger import IGameLogger
from CoreLogic.Interfaces.IDataLoader import IDataLoader


class EconomyManager:
    """
    经济管理器，管理灵魂碎片（Souls）资源。
    
    负责处理游戏中的资源获取和消耗，通过事件驱动方式工作：
    1. 监听 EntityDeathEvent 获取击杀奖励
    2. 提供鉴权接口用于建造防御塔
    3. 记录所有经济相关的日志
    
    核心功能：
    - 管理灵魂碎片余额
    - 监听敌人死亡事件并增加灵魂碎片
    - 提供 can_afford 鉴权接口
    - 提供 try_spend_souls 消费接口
    - 提供 add_souls 奖励接口
    
    使用示例：
        economy_manager = get_service(EconomyManager)
        economy_manager.initialize()  # 开始监听敌人死亡
        
        # 检查是否有足够资源
        if economy_manager.can_afford(150):
            # 尝试消费
            if economy_manager.try_spend_souls(150):
                print("消费成功")
        
        # 手动添加灵魂碎片（如关卡奖励）
        economy_manager.add_souls(500, reason="关卡奖励")
        
        # 关闭时停止监听
        economy_manager.shutdown()
    """
    
    def __init__(self, initial_souls: int = 100):
        """
        初始化经济管理器。
        
        参数：
            initial_souls: 初始灵魂碎片数量，默认 100
        """
        self._lock: Lock = Lock()
        self._souls: int = initial_souls
        self._is_initialized: bool = False
        self._logger: Optional[IGameLogger] = None
        self._data_loader: Optional[IDataLoader] = None
    
    def _get_logger(self) -> Optional[IGameLogger]:
        """
        获取日志服务。
        
        返回：
            IGameLogger 实例，如果未注册则返回 None
        """
        if self._logger is None:
            self._logger = try_get_service(IGameLogger)
        return self._logger
    
    def _get_data_loader(self) -> Optional[IDataLoader]:
        """
        获取数据加载器服务。
        
        返回：
            IDataLoader 实例，如果未注册则返回 None
        """
        if self._data_loader is None:
            self._data_loader = try_get_service(IDataLoader)
        return self._data_loader
    
    @property
    def souls(self) -> int:
        """
        获取当前灵魂碎片数量（只读）。
        
        返回：
            当前灵魂碎片余额
        """
        with self._lock:
            return self._souls
    
    def initialize(self) -> None:
        """
        初始化经济管理器，订阅 EntityDeathEvent。
        
        调用此方法后，EconomyManager 开始监听敌人死亡事件，
        当敌人死亡时自动增加灵魂碎片奖励。
        
        注意：如果已经初始化过，此方法不做任何操作。
        """
        if self._is_initialized:
            return
        
        subscribe(EntityDeathEvent, self._on_entity_death)
        self._is_initialized = True
        
        logger = self._get_logger()
        if logger is not None:
            logger.system(
                "经济系统已初始化",
                initial_souls=self._souls
            )
    
    def shutdown(self) -> None:
        """
        关闭经济管理器，取消订阅 EntityDeathEvent。
        
        调用此方法后，EconomyManager 不再监听敌人死亡事件。
        应该在系统关闭或不再需要经济系统时调用。
        
        注意：如果未初始化，此方法不做任何操作。
        """
        if not self._is_initialized:
            return
        
        unsubscribe(EntityDeathEvent, self._on_entity_death)
        self._is_initialized = False
        
        logger = self._get_logger()
        if logger is not None:
            logger.system(
                "经济系统已关闭",
                remaining_souls=self._souls
            )
    
    def is_initialized(self) -> bool:
        """
        检查经济管理器是否已初始化（正在监听事件）。
        
        返回：
            True 如果已初始化并正在监听；否则返回 False
        """
        return self._is_initialized
    
    def can_afford(self, cost: int) -> bool:
        """
        检查是否有足够的灵魂碎片。
        
        这是经济鉴权的核心接口，用于在建造防御塔或进行
        其他消耗灵魂碎片的操作前进行预检查。
        
        参数：
            cost: 需要检查的花费金额
            
        返回：
            True 如果当前灵魂碎片 >= cost；否则返回 False
            
        示例：
            # 在建造防御塔前检查
            if economy_manager.can_afford(tower_cost):
                # 可以建造
                pass
        """
        if cost < 0:
            return False
        
        with self._lock:
            return self._souls >= cost
    
    def try_spend_souls(self, cost: int, reason: str = "未知") -> bool:
        """
        尝试消耗灵魂碎片。
        
        执行原子操作：检查余额 -> 如果足够则扣除 -> 返回成功。
        
        参数：
            cost: 要消耗的灵魂碎片数量
            reason: 消耗原因，用于日志记录
            
        返回：
            True 如果消耗成功；False 如果余额不足
            
        示例：
            # 建造防御塔时消费
            if economy_manager.try_spend_souls(100, reason=f"建造{塔名}"):
                print("建造成功")
            else:
                print("灵魂碎片不足")
        """
        if cost < 0:
            return False
        
        with self._lock:
            if self._souls < cost:
                logger = self._get_logger()
                if logger is not None:
                    logger.warn(
                        "灵魂碎片不足，无法消费",
                        requested=cost,
                        current=self._souls,
                        reason=reason
                    )
                return False
            
            self._souls -= cost
            
            logger = self._get_logger()
            if logger is not None:
                logger.system(
                    "消费灵魂碎片",
                    amount=cost,
                    reason=reason,
                    remaining=self._souls
                )
            
            return True
    
    def add_souls(self, amount: int, reason: str = "奖励") -> None:
        """
        添加灵魂碎片。
        
        用于奖励机制（如击杀奖励、关卡奖励、任务奖励等）。
        
        参数：
            amount: 要添加的灵魂碎片数量
            reason: 添加原因，用于日志记录
        """
        if amount <= 0:
            return
        
        with self._lock:
            self._souls += amount
            
            logger = self._get_logger()
            if logger is not None:
                logger.system(
                    "获得灵魂碎片",
                    amount=amount,
                    reason=reason,
                    current=self._souls
                )
    
    def set_souls(self, amount: int) -> None:
        """
        直接设置灵魂碎片数量（用于加载存档等场景）。
        
        参数：
            amount: 要设置的灵魂碎片数量
        """
        with self._lock:
            old_value = self._souls
            self._souls = max(0, amount)
            
            logger = self._get_logger()
            if logger is not None:
                logger.system(
                    "灵魂碎片已重置",
                    old_value=old_value,
                    new_value=self._souls
                )
    
    def _on_entity_death(self, event: EntityDeathEvent) -> None:
        """
        处理实体死亡事件。
        
        当收到 EntityDeathEvent 时：
        1. 从数据加载器获取敌人配置
        2. 从配置中读取奖励数值
        3. 调用 add_souls 添加灵魂碎片
        
        参数：
            event: EntityDeathEvent 实例，包含死亡实体的信息
        """
        logger = self._get_logger()
        data_loader = self._get_data_loader()
        
        if data_loader is None:
            if logger is not None:
                logger.warn(
                    "无法获取敌人奖励：数据加载器未注册",
                    entity_id=event.entity_id
                )
            return
        
        reward = self._calculate_kill_reward(event.entity_id, event.max_health)
        
        if reward > 0:
            self.add_souls(reward, reason=f"击杀敌人[{event.entity_id}]")
            
            if logger is not None:
                logger.combat(
                    "击杀敌人获得灵魂碎片",
                    entity_id=event.entity_id,
                    reward=reward,
                    current_souls=self._souls
                )
    
    def _calculate_kill_reward(self, entity_id: int, max_health: float) -> int:
        """
        计算击杀奖励。
        
        策略：
        1. 优先从敌人配置中获取 reward 字段
        2. 如果无法获取配置，则使用 max_health / 10 作为备用奖励
        
        参数：
            entity_id: 死亡实体的 ID
            max_health: 实体的最大生命值
            
        返回：
            击杀奖励的灵魂碎片数量
        """
        data_loader = self._get_data_loader()
        if data_loader is None:
            return int(max_health // 10)
        
        reward_from_config = self._get_reward_from_config(entity_id)
        if reward_from_config is not None:
            return reward_from_config
        
        return int(max_health // 10)
    
    def _get_reward_from_config(self, entity_id: int) -> Optional[int]:
        """
        从数据加载器尝试获取敌人配置的奖励。
        
        注意：由于敌人实体与配置 ID 的映射可能不直接可用，
        此方法作为可扩展点，未来可以实现更精确的配置查找。
        
        参数：
            entity_id: 实体 ID
            
        返回：
            配置中的奖励值，如果无法获取则返回 None
        """
        return None
