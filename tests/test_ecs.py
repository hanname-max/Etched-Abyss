import pytest
from dataclasses import dataclass
from CoreLogic import IComponent, IEntity, IUpdateable, ITickable
from CoreLogic.ECS import BaseEntity


@dataclass
class PositionComponent:
    x: float = 0.0
    y: float = 0.0


@dataclass
class HealthComponent:
    current: int = 100
    max: int = 100


@dataclass
class VelocityComponent:
    vx: float = 0.0
    vy: float = 0.0


class TestBaseEntity:
    def setup_method(self):
        self.entity = BaseEntity(entity_id=1)

    def test_entity_id_immutable(self):
        entity = BaseEntity(entity_id=42)
        assert entity.entity_id == 42
        with pytest.raises(AttributeError):
            entity.entity_id = 100

    def test_add_and_get_component(self):
        position = PositionComponent(x=10.0, y=20.0)
        self.entity.add_component(position)
        
        retrieved = self.entity.get_component(PositionComponent)
        assert retrieved is position
        assert retrieved.x == 10.0
        assert retrieved.y == 20.0

    def test_get_nonexistent_component_returns_none(self):
        result = self.entity.get_component(PositionComponent)
        assert result is None

    def test_remove_component(self):
        self.entity.add_component(HealthComponent())
        assert self.entity.has_component(HealthComponent) is True
        
        result = self.entity.remove_component(HealthComponent)
        assert result is True
        assert self.entity.has_component(HealthComponent) is False

    def test_remove_nonexistent_component_returns_false(self):
        result = self.entity.remove_component(HealthComponent)
        assert result is False

    def test_has_component(self):
        assert self.entity.has_component(PositionComponent) is False
        
        self.entity.add_component(PositionComponent())
        assert self.entity.has_component(PositionComponent) is True

    def test_duplicate_add_replaces_component(self):
        pos1 = PositionComponent(x=1.0, y=2.0)
        pos2 = PositionComponent(x=10.0, y=20.0)
        
        self.entity.add_component(pos1)
        retrieved1 = self.entity.get_component(PositionComponent)
        assert retrieved1 is pos1
        
        self.entity.add_component(pos2)
        retrieved2 = self.entity.get_component(PositionComponent)
        assert retrieved2 is pos2
        assert retrieved2.x == 10.0
        assert retrieved2.y == 20.0

    def test_get_components_empty(self):
        components = self.entity.get_components()
        assert components == []

    def test_get_components_single(self):
        position = PositionComponent(x=5.0, y=10.0)
        self.entity.add_component(position)
        
        components = self.entity.get_components()
        assert len(components) == 1
        assert position in components

    def test_get_components_multiple(self):
        position = PositionComponent(x=1.0, y=2.0)
        health = HealthComponent(current=50, max=100)
        velocity = VelocityComponent(vx=2.0, vy=3.0)
        
        self.entity.add_component(position)
        self.entity.add_component(health)
        self.entity.add_component(velocity)
        
        components = self.entity.get_components()
        assert len(components) == 3
        assert position in components
        assert health in components
        assert velocity in components

    def test_get_components_after_removal(self):
        position = PositionComponent()
        health = HealthComponent()
        
        self.entity.add_component(position)
        self.entity.add_component(health)
        
        self.entity.remove_component(HealthComponent)
        
        components = self.entity.get_components()
        assert len(components) == 1
        assert position in components
        assert health not in components

    def test_multiple_entities_independent(self):
        entity1 = BaseEntity(entity_id=1)
        entity2 = BaseEntity(entity_id=2)
        
        entity1.add_component(PositionComponent(x=1.0, y=1.0))
        entity2.add_component(PositionComponent(x=2.0, y=2.0))
        
        assert entity1.entity_id == 1
        assert entity2.entity_id == 2
        
        pos1 = entity1.get_component(PositionComponent)
        pos2 = entity2.get_component(PositionComponent)
        
        assert pos1.x == 1.0
        assert pos2.x == 2.0

    def test_implements_ientity_interface(self):
        assert isinstance(self.entity, IEntity)

    def test_components_implement_icomponent_protocol(self):
        position = PositionComponent()
        health = HealthComponent()
        
        self.entity.add_component(position)
        self.entity.add_component(health)
        
        assert self.entity.has_component(PositionComponent)
        assert self.entity.has_component(HealthComponent)


@dataclass
class LifetimeComponent(IUpdateable):
    time: float = 0.0
    max_time: float = 5.0
    
    def update(self, delta: float) -> None:
        self.time += delta


@dataclass
class CooldownComponent(IUpdateable):
    remaining: float = 0.0
    
    def update(self, delta: float) -> None:
        if self.remaining > 0:
            self.remaining -= delta


class TestEntityManager:
    def setup_method(self):
        from CoreLogic.Managers.EntityManager import EntityManager
        self.em = EntityManager()
    
    def test_create_entity_generates_unique_ids(self):
        entity1 = self.em.create_entity()
        entity2 = self.em.create_entity()
        entity3 = self.em.create_entity()
        
        assert entity1.entity_id == 1
        assert entity2.entity_id == 2
        assert entity3.entity_id == 3
        assert entity1.entity_id != entity2.entity_id
        assert entity2.entity_id != entity3.entity_id
    
    def test_create_entity_returns_ientity_instance(self):
        entity = self.em.create_entity()
        assert isinstance(entity, IEntity)
        assert hasattr(entity, 'entity_id')
        assert hasattr(entity, 'add_component')
        assert hasattr(entity, 'get_component')
    
    def test_get_entity_returns_correct_entity(self):
        created = self.em.create_entity()
        retrieved = self.em.get_entity(created.entity_id)
        
        assert retrieved is created
        assert retrieved.entity_id == created.entity_id
    
    def test_get_nonexistent_entity_returns_none(self):
        result = self.em.get_entity(999)
        assert result is None
    
    def test_get_all_entities_returns_all_active_entities(self):
        entity1 = self.em.create_entity()
        entity2 = self.em.create_entity()
        entity3 = self.em.create_entity()
        
        all_entities = self.em.get_all_entities()
        
        assert len(all_entities) == 3
        assert entity1 in all_entities
        assert entity2 in all_entities
        assert entity3 in all_entities
    
    def test_get_all_entities_empty_when_no_entities(self):
        all_entities = self.em.get_all_entities()
        assert all_entities == []
    
    def test_destroy_entity_removes_entity(self):
        entity = self.em.create_entity()
        entity_id = entity.entity_id
        
        assert self.em.has_entity(entity_id) is True
        
        result = self.em.destroy_entity(entity_id)
        
        assert result is True
        assert self.em.has_entity(entity_id) is False
        assert self.em.get_entity(entity_id) is None
    
    def test_destroy_nonexistent_entity_returns_false(self):
        result = self.em.destroy_entity(999)
        assert result is False
    
    def test_has_entity_checks_existence(self):
        entity = self.em.create_entity()
        
        assert self.em.has_entity(entity.entity_id) is True
        assert self.em.has_entity(999) is False
        
        self.em.destroy_entity(entity.entity_id)
        assert self.em.has_entity(entity.entity_id) is False
    
    def test_get_entity_count(self):
        assert self.em.get_entity_count() == 0
        
        entity1 = self.em.create_entity()
        assert self.em.get_entity_count() == 1
        
        entity2 = self.em.create_entity()
        assert self.em.get_entity_count() == 2
        
        self.em.destroy_entity(entity1.entity_id)
        assert self.em.get_entity_count() == 1
        
        self.em.destroy_entity(entity2.entity_id)
        assert self.em.get_entity_count() == 0
    
    def test_implements_itickable_interface(self):
        assert isinstance(self.em, ITickable)
        assert hasattr(self.em, 'tick')
    
    def test_tick_calls_iupdateable_components(self):
        entity = self.em.create_entity()
        lifetime = LifetimeComponent(time=0.0, max_time=10.0)
        entity.add_component(lifetime)
        
        self.em.tick(delta=2.0)
        
        assert lifetime.time == 2.0
        
        self.em.tick(delta=3.5)
        
        assert lifetime.time == 5.5
    
    def test_tick_does_not_call_non_iupdateable_components(self):
        entity = self.em.create_entity()
        position = PositionComponent(x=10.0, y=20.0)
        entity.add_component(position)
        
        self.em.tick(delta=1.0)
        
        assert position.x == 10.0
        assert position.y == 20.0
    
    def test_multiple_iupdateable_components_in_same_entity(self):
        entity = self.em.create_entity()
        lifetime = LifetimeComponent(time=0.0, max_time=10.0)
        cooldown = CooldownComponent(remaining=5.0)
        entity.add_component(lifetime)
        entity.add_component(cooldown)
        
        self.em.tick(delta=2.0)
        
        assert lifetime.time == 2.0
        assert cooldown.remaining == 3.0
    
    def test_multiple_entities_with_iupdateable_components(self):
        entity1 = self.em.create_entity()
        lifetime1 = LifetimeComponent(time=0.0, max_time=10.0)
        entity1.add_component(lifetime1)
        
        entity2 = self.em.create_entity()
        lifetime2 = LifetimeComponent(time=0.0, max_time=20.0)
        entity2.add_component(lifetime2)
        
        self.em.tick(delta=3.0)
        
        assert lifetime1.time == 3.0
        assert lifetime2.time == 3.0
    
    def test_get_entities_with_component(self):
        entity1 = self.em.create_entity()
        entity1.add_component(PositionComponent())
        
        entity2 = self.em.create_entity()
        entity2.add_component(HealthComponent())
        
        entity3 = self.em.create_entity()
        entity3.add_component(PositionComponent())
        entity3.add_component(HealthComponent())
        
        position_entities = self.em.get_entities_with_component(PositionComponent)
        health_entities = self.em.get_entities_with_component(HealthComponent)
        
        assert len(position_entities) == 2
        assert entity1 in position_entities
        assert entity3 in position_entities
        
        assert len(health_entities) == 2
        assert entity2 in health_entities
        assert entity3 in health_entities
    
    def test_get_entities_with_component_returns_empty(self):
        entities = self.em.get_entities_with_component(PositionComponent)
        assert entities == []
    
    def test_clear_all_entities(self):
        self.em.create_entity()
        self.em.create_entity()
        self.em.create_entity()
        
        assert self.em.get_entity_count() == 3
        
        self.em.clear_all_entities()
        
        assert self.em.get_entity_count() == 0
        assert self.em.get_all_entities() == []
    
    def test_reset_resets_everything(self):
        entity1 = self.em.create_entity()
        entity2 = self.em.create_entity()
        
        self.em.reset()
        
        assert self.em.get_entity_count() == 0
        
        new_entity = self.em.create_entity()
        assert new_entity.entity_id == 1
    
    def test_negative_delta_clamped_to_zero(self):
        entity = self.em.create_entity()
        lifetime = LifetimeComponent(time=10.0, max_time=100.0)
        entity.add_component(lifetime)
        
        self.em.tick(delta=-5.0)
        
        assert lifetime.time == 10.0
    
    def test_destroy_during_tick_is_deferred(self):
        entity = self.em.create_entity()
        entity_id = entity.entity_id
        lifetime = LifetimeComponent(time=0.0, max_time=1.0)
        entity.add_component(lifetime)
        
        class DestroyOnUpdateComponent(IUpdateable):
            def __init__(self, em, entity_id):
                self.em = em
                self.entity_id = entity_id
                self.was_called = False
            
            def update(self, delta: float) -> None:
                self.was_called = True
                self.em.destroy_entity(self.entity_id)
        
        destroy_component = DestroyOnUpdateComponent(self.em, entity_id)
        entity.add_component(destroy_component)
        
        self.em.tick(delta=0.1)
        
        assert destroy_component.was_called is True
        assert lifetime.time == 0.1
        assert self.em.has_entity(entity_id) is False
    
    def test_ioc_container_integration(self):
        from CoreLogic import register_service, get_service, is_service_registered, EntityManager
        
        original_em = EntityManager()
        register_service(EntityManager, original_em)
        
        assert is_service_registered(EntityManager) is True
        
        retrieved_em = get_service(EntityManager)
        
        assert retrieved_em is original_em
        
        entity = retrieved_em.create_entity()
        assert entity.entity_id == 1
        
        from CoreLogic.Core.ServiceLocator import ServiceLocator
        ServiceLocator.reset()
