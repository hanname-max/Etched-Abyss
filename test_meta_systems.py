"""
测试元系统：经济系统、疯狂值系统和事件总线闭环
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from CoreLogic.Events.OnHighInsanityEvent import OnHighInsanityEvent
from CoreLogic.Managers.EconomyManager import EconomyManager
from CoreLogic.Managers.InsanityManager import InsanityManager

from CoreLogic import (
    EconomyManager as CEconomyManager,
    InsanityManager as CInsanityManager,
    OnHighInsanityEvent as COnHighInsanityEvent,
    subscribe,
    publish,
)


def test_imports():
    print("Testing imports...")
    assert OnHighInsanityEvent is not None
    assert EconomyManager is not None
    assert InsanityManager is not None
    assert CEconomyManager is not None
    assert CInsanityManager is not None
    assert COnHighInsanityEvent is not None
    print("  [OK] All imports successful")


def test_on_high_insanity_event():
    print("\nTesting OnHighInsanityEvent...")
    event = OnHighInsanityEvent(
        current_insanity=85.0,
        is_high_insanity=True,
        threshold=80.0
    )
    assert event.current_insanity == 85.0
    assert event.is_high_insanity is True
    assert event.threshold == 80.0
    
    event2 = OnHighInsanityEvent(
        current_insanity=75.0,
        is_high_insanity=False
    )
    assert event2.current_insanity == 75.0
    assert event2.is_high_insanity is False
    assert event2.threshold == 80.0
    
    print("  [OK] OnHighInsanityEvent works correctly")


def test_economy_manager():
    print("\nTesting EconomyManager...")
    
    economy = EconomyManager(initial_souls=100)
    assert economy.souls == 100
    print(f"  Initial souls: {economy.souls}")
    
    assert economy.can_afford(50) is True
    assert economy.can_afford(200) is False
    print("  [OK] can_afford works correctly")
    
    economy.add_souls(50, reason="test reward")
    assert economy.souls == 150
    print(f"  After add_souls(50): {economy.souls}")
    
    success = economy.try_spend_souls(75, reason="test purchase")
    assert success is True
    assert economy.souls == 75
    print(f"  After try_spend_souls(75): {economy.souls}")
    
    success = economy.try_spend_souls(200, reason="test purchase too expensive")
    assert success is False
    assert economy.souls == 75
    print("  [OK] try_spend_souls fails correctly when not enough souls")
    
    economy.set_souls(500)
    assert economy.souls == 500
    print(f"  After set_souls(500): {economy.souls}")
    
    print("  [OK] EconomyManager works correctly")


def test_insanity_manager():
    print("\nTesting InsanityManager...")
    
    insanity = InsanityManager(initial_insanity=0.0)
    assert insanity.insanity == 0.0
    assert insanity.is_high_insanity() is False
    assert insanity.HIGH_INSANITY_THRESHOLD == 80.0
    assert insanity.high_insanity_damage_multiplier == 1.5
    assert insanity.high_insanity_search_radius_multiplier == 0.5
    print(f"  Initial insanity: {insanity.insanity}")
    print(f"  Is high insanity: {insanity.is_high_insanity()}")
    
    insanity.add_insanity(30.0, reason="equip organ 1")
    assert insanity.insanity == 30.0
    assert insanity.is_high_insanity() is False
    print(f"  After add_insanity(30): {insanity.insanity}")
    
    insanity.add_insanity(55.0, reason="equip organ 2")
    assert insanity.insanity == 85.0
    assert insanity.is_high_insanity() is True
    print(f"  After add_insanity(55): {insanity.insanity}")
    print(f"  Is high insanity: {insanity.is_high_insanity()}")
    
    insanity.remove_insanity(10.0, reason="unequip organ")
    assert insanity.insanity == 75.0
    assert insanity.is_high_insanity() is False
    print(f"  After remove_insanity(10): {insanity.insanity}")
    print(f"  Is high insanity: {insanity.is_high_insanity()}")
    
    insanity.set_insanity(100.0)
    assert insanity.insanity == 100.0
    assert insanity.is_high_insanity() is True
    print(f"  After set_insanity(100): {insanity.insanity}")
    
    insanity.set_insanity(-10.0)
    assert insanity.insanity == 0.0
    print(f"  After set_insanity(-10): {insanity.insanity} (clamped to 0)")
    
    insanity.set_insanity(200.0)
    assert insanity.insanity == 100.0
    print(f"  After set_insanity(200): {insanity.insanity} (clamped to 100)")
    
    print("  [OK] InsanityManager works correctly")


def test_event_bus_integration():
    print("\nTesting EventBus integration...")
    
    from CoreLogic.Core.EventBus import EventBus
    EventBus.reset()
    
    received_events = []
    
    def on_high_insanity_handler(event):
        received_events.append(event)
        print(f"  [Handler] Received event: current_insanity={event.current_insanity}, is_high_insanity={event.is_high_insanity}")
    
    subscribe(OnHighInsanityEvent, on_high_insanity_handler)
    
    insanity = InsanityManager(initial_insanity=0.0)
    insanity.initialize()
    
    print("  Adding 85 insanity...")
    insanity.add_insanity(85.0, reason="test")
    
    assert len(received_events) == 1
    assert received_events[0].is_high_insanity is True
    assert received_events[0].current_insanity == 85.0
    print("  [OK] Entering high insanity event published")
    
    print("  Removing 10 insanity...")
    insanity.remove_insanity(10.0, reason="test")
    
    assert len(received_events) == 2
    assert received_events[1].is_high_insanity is False
    assert received_events[1].current_insanity == 75.0
    print("  [OK] Exiting high insanity event published")
    
    insanity.shutdown()
    EventBus.reset()
    
    print("  [OK] EventBus integration works correctly")


def test_organ_config_insanity_gain():
    print("\nTesting OrganConfigDTO insanity_gain...")
    
    from CoreLogic.DTOs.OrganConfigDTO import OrganConfigDTO
    
    normal_organ = OrganConfigDTO(
        id="organ_normal_001",
        name="普通器官",
        description="不增加疯狂值",
        attribute_modifiers=[]
    )
    assert normal_organ.insanity_gain == 0.0
    print(f"  Normal organ insanity_gain: {normal_organ.insanity_gain}")
    
    ancient_eye = OrganConfigDTO(
        id="organ_ancient_eye_001",
        name="古神视神经",
        description="来自深渊的凝视",
        attribute_modifiers=[
            {"attribute": "attack_range", "value": 2.0, "type": "additive"}
        ],
        insanity_gain=25.0
    )
    assert ancient_eye.insanity_gain == 25.0
    print(f"  Ancient eye insanity_gain: {ancient_eye.insanity_gain}")
    
    print("  [OK] OrganConfigDTO insanity_gain works correctly")


def main():
    print("=" * 60)
    print("Testing Global Meta Systems")
    print("=" * 60)
    
    test_imports()
    test_on_high_insanity_event()
    test_economy_manager()
    test_insanity_manager()
    test_event_bus_integration()
    test_organ_config_insanity_gain()
    
    print("\n" + "=" * 60)
    print("[PASS] All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
