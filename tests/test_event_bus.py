import pytest
from CoreLogic import (
    EventBus,
    subscribe,
    unsubscribe,
    publish,
)


class EnemyKilledEvent:
    def __init__(self, enemy_id: str, reward: int):
        self.enemy_id = enemy_id
        self.reward = reward


class PlayerDamagedEvent:
    def __init__(self, damage: int, remaining_hp: int):
        self.damage = damage
        self.remaining_hp = remaining_hp


class TestEventBus:
    def setup_method(self):
        EventBus.reset()
    
    def test_singleton_behavior(self):
        bus1 = EventBus()
        bus2 = EventBus()
        assert bus1 is bus2
    
    def test_subscribe_and_publish_single_handler(self):
        received_events = []
        
        def handler(event: EnemyKilledEvent):
            received_events.append(event)
        
        subscribe(EnemyKilledEvent, handler)
        
        event = EnemyKilledEvent(enemy_id="enemy_001", reward=100)
        publish(event)
        
        assert len(received_events) == 1
        assert received_events[0].enemy_id == "enemy_001"
        assert received_events[0].reward == 100
    
    def test_subscribe_and_publish_multiple_handlers(self):
        call_order = []
        
        def handler1(event: EnemyKilledEvent):
            call_order.append("handler1")
        
        def handler2(event: EnemyKilledEvent):
            call_order.append("handler2")
        
        def handler3(event: EnemyKilledEvent):
            call_order.append("handler3")
        
        subscribe(EnemyKilledEvent, handler1)
        subscribe(EnemyKilledEvent, handler2)
        subscribe(EnemyKilledEvent, handler3)
        
        publish(EnemyKilledEvent(enemy_id="e1", reward=50))
        
        assert call_order == ["handler1", "handler2", "handler3"]
    
    def test_unsubscribe_removes_handler(self):
        received_events = []
        
        def handler(event: EnemyKilledEvent):
            received_events.append(event)
        
        subscribe(EnemyKilledEvent, handler)
        publish(EnemyKilledEvent(enemy_id="e1", reward=50))
        assert len(received_events) == 1
        
        unsubscribe(EnemyKilledEvent, handler)
        publish(EnemyKilledEvent(enemy_id="e2", reward=100))
        assert len(received_events) == 1
    
    def test_unsubscribe_nonexistent_handler_no_error(self):
        def handler(event: EnemyKilledEvent):
            pass
        
        unsubscribe(EnemyKilledEvent, handler)
    
    def test_event_type_isolation(self):
        enemy_events = []
        damage_events = []
        
        def enemy_handler(event: EnemyKilledEvent):
            enemy_events.append(event)
        
        def damage_handler(event: PlayerDamagedEvent):
            damage_events.append(event)
        
        subscribe(EnemyKilledEvent, enemy_handler)
        subscribe(PlayerDamagedEvent, damage_handler)
        
        publish(EnemyKilledEvent(enemy_id="e1", reward=50))
        publish(PlayerDamagedEvent(damage=10, remaining_hp=90))
        publish(EnemyKilledEvent(enemy_id="e2", reward=30))
        
        assert len(enemy_events) == 2
        assert len(damage_events) == 1
        assert enemy_events[0].enemy_id == "e1"
        assert enemy_events[1].enemy_id == "e2"
        assert damage_events[0].damage == 10
    
    def test_publish_is_synchronous(self):
        execution_order = []
        
        def handler(event: EnemyKilledEvent):
            execution_order.append("handler")
        
        subscribe(EnemyKilledEvent, handler)
        
        execution_order.append("before_publish")
        publish(EnemyKilledEvent(enemy_id="e1", reward=50))
        execution_order.append("after_publish")
        
        assert execution_order == ["before_publish", "handler", "after_publish"]
    
    def test_clear_all_subscribers(self):
        received_events = []
        
        def handler(event: EnemyKilledEvent):
            received_events.append(event)
        
        subscribe(EnemyKilledEvent, handler)
        
        bus = EventBus()
        bus.clear_all()
        
        publish(EnemyKilledEvent(enemy_id="e1", reward=50))
        assert len(received_events) == 0
    
    def test_get_subscriber_count(self):
        def handler1(event: EnemyKilledEvent):
            pass
        
        def handler2(event: EnemyKilledEvent):
            pass
        
        bus = EventBus()
        
        assert bus.get_subscriber_count(EnemyKilledEvent) == 0
        
        subscribe(EnemyKilledEvent, handler1)
        assert bus.get_subscriber_count(EnemyKilledEvent) == 1
        
        subscribe(EnemyKilledEvent, handler2)
        assert bus.get_subscriber_count(EnemyKilledEvent) == 2
        
        unsubscribe(EnemyKilledEvent, handler1)
        assert bus.get_subscriber_count(EnemyKilledEvent) == 1
    
    def test_same_handler_subscribed_multiple_times(self):
        call_count = 0
        
        def handler(event: EnemyKilledEvent):
            nonlocal call_count
            call_count += 1
        
        subscribe(EnemyKilledEvent, handler)
        subscribe(EnemyKilledEvent, handler)
        subscribe(EnemyKilledEvent, handler)
        
        publish(EnemyKilledEvent(enemy_id="e1", reward=50))
        
        assert call_count == 3
    
    def test_unsubscribe_first_occurrence(self):
        call_count = 0
        
        def handler(event: EnemyKilledEvent):
            nonlocal call_count
            call_count += 1
        
        subscribe(EnemyKilledEvent, handler)
        subscribe(EnemyKilledEvent, handler)
        
        publish(EnemyKilledEvent(enemy_id="e1", reward=50))
        assert call_count == 2
        
        unsubscribe(EnemyKilledEvent, handler)
        publish(EnemyKilledEvent(enemy_id="e2", reward=50))
        assert call_count == 3
