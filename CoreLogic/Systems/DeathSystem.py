"""
死亡系统

DeathSystem 负责处理实体的死亡流程，通过 EventBus 订阅 EntityDeathEvent，
并调用 EntityManager 销毁死亡的实体。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯事件驱动的系统，不负责每帧更新，而是通过订阅死亡事件来工作。

关键设计决策（解耦性最强的方案）：
1. HealthSystem 检测死亡并发布 EntityDeathEvent
2. DeathSystem 订阅 EntityDeathEvent
3. DeathSystem 通过 ServiceLocator 获取 EntityManager
4. DeathSystem 调用 destroy_entity 销毁实体

这样的设计实现了最大程度的解耦：
- HealthSystem 不需要知道 EntityManager 的存在
- EntityManager 不需要知道 HealthSystem 的存在
- 其他系统（经济系统、成就系统等）也可以独立订阅 EntityDeathEvent

使用示例：
    # 初始化并启动死亡系统
    death_system = DeathSystem()
    death_system.initialize()  # 订阅 EntityDeathEvent
    
    # 当 HealthSystem 发布 EntityDeathEvent 时，
    # DeathSystem 会自动捕获并销毁实体
    
    # 销毁时停止监听
    death_system.shutdown()  # 取消订阅
============================================================================
"""

from typing import Optional

from CoreLogic import (
    subscribe,
    unsubscribe,
    EntityDeathEvent,
    EntityManager,
    try_get_service,
)


class DeathSystem:
    """
    死亡系统。
    
    负责监听 EntityDeathEvent 并调用 EntityManager 销毁死亡实体。
    这是一个纯事件驱动的系统，不实现 ITickable 接口。
    
    特性：
    - 事件驱动：不每帧更新，仅在收到死亡事件时工作
    - 完全解耦：通过 EventBus 和 ServiceLocator 与其他系统通信
    - 灵活可控：可随时调用 initialize() 和 shutdown() 来启停
    
    使用示例：
        death_system = DeathSystem()
        death_system.initialize()  # 开始监听死亡事件
        
        # 此时任何实体死亡都会被自动销毁
        
        death_system.shutdown()  # 停止监听
    """
    
    def __init__(self) -> None:
        """
        初始化死亡系统。
        
        注意：这只是创建实例，需要手动调用 initialize() 开始监听事件。
        """
        self._is_initialized: bool = False
    
    def initialize(self) -> None:
        """
        初始化死亡系统，订阅 EntityDeathEvent。
        
        调用此方法后，DeathSystem 开始监听死亡事件。
        当收到 EntityDeathEvent 时，会尝试获取 EntityManager 并销毁实体。
        
        注意：如果已经初始化过，此方法不做任何操作。
        """
        if self._is_initialized:
            return
        
        subscribe(EntityDeathEvent, self._on_entity_death)
        self._is_initialized = True
    
    def shutdown(self) -> None:
        """
        关闭死亡系统，取消订阅 EntityDeathEvent。
        
        调用此方法后，DeathSystem 不再监听死亡事件。
        应该在系统关闭或不再需要死亡处理时调用。
        
        注意：如果未初始化，此方法不做任何操作。
        """
        if not self._is_initialized:
            return
        
        unsubscribe(EntityDeathEvent, self._on_entity_death)
        self._is_initialized = False
    
    def is_initialized(self) -> bool:
        """
        检查死亡系统是否已初始化（正在监听事件）。
        
        返回：
            True 如果已初始化并正在监听；否则返回 False
        """
        return self._is_initialized
    
    def _get_entity_manager(self) -> Optional[EntityManager]:
        """
        从 ServiceLocator 获取 EntityManager。
        
        返回：
            EntityManager 实例，如果未注册则返回 None
        """
        return try_get_service(EntityManager)
    
    def _on_entity_death(self, event: EntityDeathEvent) -> None:
        """
        处理实体死亡事件。
        
        当收到 EntityDeathEvent 时：
        1. 从 ServiceLocator 获取 EntityManager
        2. 调用 destroy_entity 销毁该实体
        
        参数：
            event: EntityDeathEvent 实例，包含死亡实体的信息
        """
        entity_manager = self._get_entity_manager()
        if entity_manager is None:
            return
        
        entity_manager.destroy_entity(event.entity_id)
