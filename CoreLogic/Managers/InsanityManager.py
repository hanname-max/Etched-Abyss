"""
疯狂值管理器

InsanityManager 负责管理游戏中的全局疯狂值系统。

============================================================================
【架构规范强制声明】
============================================================================

InsanityManager 应该通过 ServiceLocator 获取，而不是直接实例化。
它依赖以下服务（必须预先注册到 ServiceLocator）：
- IGameLogger: 用于记录疯狂值变化日志

此管理器：
1. 管理全局疯狂值（范围 0~100）
2. 监听器官装备/卸下事件来调整疯狂值
3. 当疯狂值超过阈值（默认 80）时发布 OnHighInsanityEvent
4. 当疯狂值回落至阈值以下时也发布 OnHighInsanityEvent

正确示例：
    from CoreLogic import get_service, register_service, InsanityManager, IGameLogger, GameLogger
    
    # 注册依赖服务
    register_service(IGameLogger, GameLogger())
    register_service(InsanityManager, InsanityManager())
    
    # 使用
    insanity_manager = get_service(InsanityManager)
    insanity_manager.initialize()  # 开始监听器官事件
    
    # 当装备疯狂器官时
    insanity_manager.add_insanity(25.0, reason="装备古神视神经")
    
    # 检查当前状态
    if insanity_manager.is_high_insanity():
        print("系统处于高疯狂状态！")
============================================================================
"""

from threading import Lock
from typing import Optional, Set
from uuid import UUID

from CoreLogic.Events.OnHighInsanityEvent import OnHighInsanityEvent
from CoreLogic.Core.ServiceLocator import try_get_service
from CoreLogic.Core.EventBus import publish
from CoreLogic.Interfaces.IGameLogger import IGameLogger


class InsanityManager:
    """
    疯狂值管理器，管理全局疯狂值状态。
    
    负责处理游戏中的疯狂值获取和消耗，实现高风险高回报机制：
    1. 管理全局疯狂值（范围 0~100）
    2. 当疯狂值 > 80 时进入"高疯狂状态"
    3. 高疯狂状态下：塔的索敌距离减半，但攻击力获得 1.5 倍乘区
    4. 通过 OnHighInsanityEvent 通知所有订阅者
    
    核心功能：
    - 管理疯狂值余额（0~100）
    - 提供 add_insanity 和 remove_insanity 方法
    - 跟踪高疯狂状态的进入和退出
    - 发布 OnHighInsanityEvent 通知其他系统
    
    疯狂值来源：
    - 装备极端器官（如"古神视神经"）
    - 使用某些技能或道具
    - 特定事件触发
    
    使用示例：
        insanity_manager = get_service(InsanityManager)
        insanity_manager.initialize()
        
        # 装备疯狂器官时增加疯狂值
        insanity_manager.add_insanity(30.0, reason="装备古神视神经")
        
        # 检查当前疯狂值
        print(f"当前疯狂值: {insanity_manager.insanity}")
        
        # 检查是否处于高疯狂状态
        if insanity_manager.is_high_insanity():
            print("⚠️ 系统进入高疯狂状态！")
            print("索敌距离减半，攻击力 x1.5")
        
        # 卸下疯狂器官时减少疯狂值
        insanity_manager.remove_insanity(30.0, reason="卸下古神视神经")
    """
    
    HIGH_INSANITY_THRESHOLD: float = 80.0
    MAX_INSANITY: float = 100.0
    MIN_INSANITY: float = 0.0
    
    def __init__(self, initial_insanity: float = 0.0):
        """
        初始化疯狂值管理器。
        
        参数：
            initial_insanity: 初始疯狂值，默认 0.0
        """
        self._lock: Lock = Lock()
        self._insanity: float = self._clamp(initial_insanity)
        self._is_high_insanity: bool = False
        self._is_initialized: bool = False
        self._logger: Optional[IGameLogger] = None
        
        self._high_insanity_damage_multiplier: float = 1.5
        self._high_insanity_search_radius_multiplier: float = 0.5
        self._active_modifiers: Set[UUID] = set()
    
    def _get_logger(self) -> Optional[IGameLogger]:
        """
        获取日志服务。
        
        返回：
            IGameLogger 实例，如果未注册则返回 None
        """
        if self._logger is None:
            self._logger = try_get_service(IGameLogger)
        return self._logger
    
    def _clamp(self, value: float) -> float:
        """
        将疯狂值限制在有效范围内（0~100）。
        
        参数：
            value: 原始值
            
        返回：
            限制后的值
        """
        return max(self.MIN_INSANITY, min(self.MAX_INSANITY, value))
    
    @property
    def insanity(self) -> float:
        """
        获取当前疯狂值（只读）。
        
        返回：
            当前疯狂值（0~100）
        """
        with self._lock:
            return self._insanity
    
    @property
    def high_insanity_damage_multiplier(self) -> float:
        """
        获取高疯狂状态下的伤害乘区系数。
        
        返回：
            伤害乘区系数（默认 1.5）
        """
        return self._high_insanity_damage_multiplier
    
    @property
    def high_insanity_search_radius_multiplier(self) -> float:
        """
        获取高疯狂状态下的索敌距离乘区系数。
        
        返回：
            索敌距离乘区系数（默认 0.5，即减半）
        """
        return self._high_insanity_search_radius_multiplier
    
    def initialize(self) -> None:
        """
        初始化疯狂值管理器。
        
        检查初始疯狂值是否超过阈值，如果超过则触发高疯狂状态。
        """
        if self._is_initialized:
            return
        
        self._is_initialized = True
        
        with self._lock:
            if self._insanity >= self.HIGH_INSANITY_THRESHOLD:
                self._is_high_insanity = True
                self._publish_high_insanity_event(True)
        
        logger = self._get_logger()
        if logger is not None:
            logger.system(
                "疯狂值系统已初始化",
                initial_insanity=self._insanity,
                threshold=self.HIGH_INSANITY_THRESHOLD
            )
    
    def shutdown(self) -> None:
        """
        关闭疯狂值管理器。
        
        清理所有状态，停止监听事件。
        """
        if not self._is_initialized:
            return
        
        self._is_initialized = False
        
        with self._lock:
            if self._is_high_insanity:
                self._is_high_insanity = False
                self._publish_high_insanity_event(False)
        
        logger = self._get_logger()
        if logger is not None:
            logger.system(
                "疯狂值系统已关闭",
                final_insanity=self._insanity
            )
    
    def is_initialized(self) -> bool:
        """
        检查疯狂值管理器是否已初始化。
        
        返回：
            True 如果已初始化；否则返回 False
        """
        return self._is_initialized
    
    def is_high_insanity(self) -> bool:
        """
        检查当前是否处于高疯狂状态。
        
        返回：
            True 如果疯狂值 >= 阈值（默认 80）；否则返回 False
        """
        with self._lock:
            return self._is_high_insanity
    
    def _change_insanity(self, delta: float, reason: str) -> None:
        """
        内部方法：改变疯狂值（支持增加和减少）。
        
        参数：
            delta: 变化量（正数为增加，负数为减少）
            reason: 变化原因，用于日志记录
        """
        with self._lock:
            old_insanity = self._insanity
            old_is_high = self._is_high_insanity
            
            self._insanity = self._clamp(self._insanity + delta)
            
            new_is_high = self._insanity >= self.HIGH_INSANITY_THRESHOLD
            
            if not old_is_high and new_is_high:
                self._is_high_insanity = True
                self._publish_high_insanity_event(True)
                
                logger = self._get_logger()
                if logger is not None:
                    logger.system(
                        "进入高疯狂状态",
                        previous_insanity=old_insanity,
                        current_insanity=self._insanity,
                        threshold=self.HIGH_INSANITY_THRESHOLD,
                        reason=reason
                    )
            
            elif old_is_high and not new_is_high:
                self._is_high_insanity = False
                self._publish_high_insanity_event(False)
                
                logger = self._get_logger()
                if logger is not None:
                    logger.system(
                        "高疯狂状态解除",
                        previous_insanity=old_insanity,
                        current_insanity=self._insanity,
                        threshold=self.HIGH_INSANITY_THRESHOLD,
                        reason=reason
                    )
            
            logger = self._get_logger()
            if logger is not None:
                if delta > 0:
                    logger.system(
                        "疯狂值增加",
                        amount=delta,
                        previous=old_insanity,
                        current=self._insanity,
                        reason=reason
                    )
                elif delta < 0:
                    logger.system(
                        "疯狂值减少",
                        amount=-delta,
                        previous=old_insanity,
                        current=self._insanity,
                        reason=reason
                    )
    
    def add_insanity(self, amount: float, reason: str = "未知") -> None:
        """
        增加疯狂值。
        
        当疯狂值从低于阈值增加到高于阈值时，
        会发布 OnHighInsanityEvent 通知进入高疯狂状态。
        
        参数：
            amount: 要增加的疯狂值数量（正数）
            reason: 增加原因，用于日志记录
        """
        if amount <= 0:
            return
        
        self._change_insanity(amount, reason)
    
    def remove_insanity(self, amount: float, reason: str = "未知") -> None:
        """
        减少疯狂值。
        
        当疯狂值从高于阈值减少到低于阈值时，
        会发布 OnHighInsanityEvent 通知退出高疯狂状态。
        
        参数：
            amount: 要减少的疯狂值数量（正数）
            reason: 减少原因，用于日志记录
        """
        if amount <= 0:
            return
        
        self._change_insanity(-amount, reason)
    
    def set_insanity(self, value: float) -> None:
        """
        直接设置疯狂值（用于加载存档等场景）。
        
        参数：
            value: 要设置的疯狂值（将被限制在 0~100 范围内）
        """
        with self._lock:
            old_insanity = self._insanity
            old_is_high = self._is_high_insanity
            
            self._insanity = self._clamp(value)
            
            new_is_high = self._insanity >= self.HIGH_INSANITY_THRESHOLD
            
            if old_is_high != new_is_high:
                self._is_high_insanity = new_is_high
                self._publish_high_insanity_event(new_is_high)
                
                logger = self._get_logger()
                if logger is not None:
                    if new_is_high:
                        logger.system(
                            "⚠️ 进入高疯狂状态（直接设置）",
                            previous_insanity=old_insanity,
                            current_insanity=self._insanity,
                            threshold=self.HIGH_INSANITY_THRESHOLD
                        )
                    else:
                        logger.system(
                            "高疯狂状态解除（直接设置）",
                            previous_insanity=old_insanity,
                            current_insanity=self._insanity,
                            threshold=self.HIGH_INSANITY_THRESHOLD
                        )
            
            logger = self._get_logger()
            if logger is not None:
                logger.system(
                    "疯狂值已重置",
                    old_value=old_insanity,
                    new_value=self._insanity
                )
    
    def _publish_high_insanity_event(self, is_entering: bool) -> None:
        """
        发布高疯狂值事件。
        
        此方法在持有锁的情况下调用，因为它被 add_insanity 和 set_insanity 调用，
        这两个方法已经持有了锁。
        
        参数：
            is_entering: True 表示进入高疯狂状态，False 表示退出
        """
        event = OnHighInsanityEvent(
            current_insanity=self._insanity,
            is_high_insanity=is_entering,
            threshold=self.HIGH_INSANITY_THRESHOLD
        )
        publish(event)
        
        logger = self._get_logger()
        if logger is not None:
            if is_entering:
                logger.combat(
                    "⚡ 发布高疯狂状态事件",
                    current_insanity=self._insanity,
                    threshold=self.HIGH_INSANITY_THRESHOLD,
                    damage_multiplier=self._high_insanity_damage_multiplier,
                    search_radius_multiplier=self._high_insanity_search_radius_multiplier
                )
            else:
                logger.combat(
                    "发布高疯狂状态解除事件",
                    current_insanity=self._insanity,
                    threshold=self.HIGH_INSANITY_THRESHOLD
                )
    
    def register_modifier(self, modifier_id: UUID) -> None:
        """
        注册一个活动的修饰器 ID。
        
        用于跟踪哪些实体已经应用了高疯狂状态修饰器，
        避免重复应用或错误移除。
        
        参数：
            modifier_id: 修饰器的 UUID
        """
        with self._lock:
            self._active_modifiers.add(modifier_id)
    
    def unregister_modifier(self, modifier_id: UUID) -> None:
        """
        注销一个活动的修饰器 ID。
        
        参数：
            modifier_id: 修饰器的 UUID
        """
        with self._lock:
            self._active_modifiers.discard(modifier_id)
    
    def is_modifier_active(self, modifier_id: UUID) -> bool:
        """
        检查指定修饰器 ID 是否处于活动状态。
        
        参数：
            modifier_id: 修饰器的 UUID
            
        返回：
            True 如果修饰器已注册；否则返回 False
        """
        with self._lock:
            return modifier_id in self._active_modifiers
