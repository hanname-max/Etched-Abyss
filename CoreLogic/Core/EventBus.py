"""
全局事件总线（Event Bus）实现

提供纯粹的、同步的发布-订阅（Pub/Sub）系统，用于模块间解耦通信。

============================================================================
【架构规范强制声明】
============================================================================

不同域（如战斗系统、经济系统、UI系统、存档系统等）之间的交互，
必须通过投递 Event 进行，严禁跨域的强耦合直接调用。

正确示例：
    # 战斗系统发布事件
    event_bus.publish(EnemyKilledEvent(enemy_id="enemy_001", reward=100))
    
    # 经济系统订阅并处理
    event_bus.subscribe(EnemyKilledEvent, self._on_enemy_killed)
    
错误示例（严禁使用）：
    # 战斗系统直接调用经济系统方法（强耦合）
    self.economic_system.add_gold(100)

违反此规范的代码将被视为架构缺陷，需要重构。
============================================================================
"""

from typing import Type, TypeVar, Callable, Dict, List, Any
from CoreLogic.Interfaces.IEvent import IEvent


TEvent = TypeVar('TEvent', bound=IEvent)
EventHandler = Callable[[TEvent], None]


class EventBus:
    """
    全局事件总线，实现同步的发布-订阅模式。
    
    特性：
    - 类型安全：订阅和发布都基于事件类型
    - 同步执行：发布事件时立即同步调用所有订阅者
    - 线程安全：在单线程游戏逻辑中使用，无需额外同步
    
    使用示例：
        # 订阅事件
        event_bus.subscribe(EnemyKilledEvent, self._handle_enemy_killed)
        
        # 发布事件（同步执行所有订阅者）
        event_bus.publish(EnemyKilledEvent(enemy_id="e1", reward=50))
        
        # 取消订阅
        event_bus.unsubscribe(EnemyKilledEvent, self._handle_enemy_killed)
    """
    
    _instance: 'EventBus | None' = None
    
    def __new__(cls) -> 'EventBus':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers: Dict[Type[IEvent], List[EventHandler[Any]]] = {}
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """
        重置事件总线单例（仅用于测试）。
        """
        if cls._instance is not None:
            cls._instance._subscribers.clear()
        cls._instance = None
    
    def subscribe(self, event_type: Type[TEvent], handler: EventHandler[TEvent]) -> None:
        """
        订阅指定类型的事件。
        
        当该类型的事件被发布时，handler 将被同步调用。
        
        Args:
            event_type: 要订阅的事件类型（类对象，不是实例）
            handler: 事件处理函数，签名为 def handler(event: TEvent) -> None
        
        示例：
            event_bus.subscribe(EnemyKilledEvent, self._on_enemy_killed)
        
        注意：
            - 同一个 handler 可以多次订阅同一事件类型，每次都会被调用
            - handler 是同步执行的，应避免在 handler 中执行耗时操作
            - handler 中可以发布新事件，但要注意避免无限递归
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def unsubscribe(self, event_type: Type[TEvent], handler: EventHandler[TEvent]) -> None:
        """
        取消订阅指定类型的事件。
        
        移除指定的 handler，使其不再接收该类型的事件。
        
        Args:
            event_type: 要取消订阅的事件类型
            handler: 要移除的事件处理函数
        
        示例：
            event_bus.unsubscribe(EnemyKilledEvent, self._on_enemy_killed)
        
        注意：
            - 如果 handler 未订阅该事件类型，此操作不产生任何效果
            - 如果 handler 多次订阅，只会移除第一个匹配的实例
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
            except ValueError:
                pass
    
    def publish(self, event: TEvent) -> None:
        """
        发布一个事件，同步调用所有订阅者。
        
        所有订阅了该事件类型的 handler 将按照订阅顺序依次同步执行。
        
        Args:
            event: 要发布的事件实例
        
        示例：
            event_bus.publish(EnemyKilledEvent(enemy_id="e1", reward=50))
        
        注意：
            - 这是同步操作：publish 返回时，所有订阅者都已执行完毕
            - 订阅者的执行顺序：先订阅的先执行
            - 如果某个订阅者抛出异常，后续的订阅者不会被调用
            - 可以在订阅者中发布新事件，但要注意避免无限递归
            - 发布事件时，事件类型的精确匹配：订阅 BaseEvent 的不会收到 DerivedEvent
        """
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in list(self._subscribers[event_type]):
                handler(event)
    
    def clear_all(self) -> None:
        """
        清除所有订阅（仅用于测试）。
        """
        self._subscribers.clear()
    
    def get_subscriber_count(self, event_type: Type[IEvent]) -> int:
        """
        获取指定事件类型的订阅者数量（仅用于测试）。
        
        Args:
            event_type: 事件类型
            
        Returns:
            订阅者的数量
        """
        return len(self._subscribers.get(event_type, []))


def subscribe(event_type: Type[TEvent], handler: EventHandler[TEvent]) -> None:
    """
    订阅指定类型的事件（便捷函数）。
    
    使用全局 EventBus 单例进行订阅。
    
    Args:
        event_type: 要订阅的事件类型
        handler: 事件处理函数
    """
    bus = EventBus()
    bus.subscribe(event_type, handler)


def unsubscribe(event_type: Type[TEvent], handler: EventHandler[TEvent]) -> None:
    """
    取消订阅指定类型的事件（便捷函数）。
    
    使用全局 EventBus 单例取消订阅。
    
    Args:
        event_type: 要取消订阅的事件类型
        handler: 要移除的事件处理函数
    """
    bus = EventBus()
    bus.unsubscribe(event_type, handler)


def publish(event: TEvent) -> None:
    """
    发布一个事件（便捷函数）。
    
    使用全局 EventBus 单例发布事件，同步调用所有订阅者。
    
    Args:
        event: 要发布的事件实例
    """
    bus = EventBus()
    bus.publish(event)
