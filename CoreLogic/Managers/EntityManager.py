"""
实体管理器实现

EntityManager 是全局的实体生命周期注册中心，负责：
1. 统一生成 Entity 的唯一 ID
2. 提供 CreateEntity() 和 DestroyEntity(id) 方法
3. 维护活动实体的集合
4. 提供 GetEntity(id) 和 GetAllEntities() 接口
5. 实现 Update(deltaTime) 方法，自动调用 IUpdateable 组件

============================================================================
【架构规范强制声明】
============================================================================

EntityManager 应该通过 ServiceLocator 获取，而不是直接实例化。
它实现了 ITickable 接口，应该注册到 GameLoopManager 以获得每帧更新。

正确示例：
    from CoreLogic import get_service, register_service, EntityManager, GameLoopManager
    
    # 注册到 IoC 容器
    entity_manager = EntityManager()
    register_service(EntityManager, entity_manager)
    
    # 注册到 GameLoopManager 以获得更新
    loop_manager = get_service(GameLoopManager)
    loop_manager.register_tickable(entity_manager)
    
    # 使用
    em = get_service(EntityManager)
    entity = em.create_entity()
    entity.add_component(SomeComponent())
    em.destroy_entity(entity.entity_id)

错误示例（严禁使用）：
    # 直接实例化多个 EntityManager
    em1 = EntityManager()
    em2 = EntityManager()  # 这会导致 ID 生成冲突
============================================================================
"""

from typing import Dict, List, Optional, Set, Type
from threading import Lock

from CoreLogic.ECS.BaseEntity import BaseEntity
from CoreLogic.Interfaces.IEntity import IEntity
from CoreLogic.Interfaces.IUpdateable import IUpdateable
from CoreLogic.Interfaces.ITickable import ITickable


class EntityManager(ITickable):
    """
    实体管理器。
    
    全局的实体生命周期注册中心，负责实体的创建、销毁、查询和更新。
    
    核心功能：
    1. 线程安全的唯一 ID 生成
    2. 实体的创建和销毁（支持延迟销毁）
    3. 实体的查询（按 ID、按组件类型）
    4. 自动更新 IUpdateable 组件
    
    使用示例：
        em = EntityManager()
        
        # 创建实体
        entity1 = em.create_entity()
        entity2 = em.create_entity()
        
        # 添加组件
        entity1.add_component(PositionComponent(x=0, y=0))
        entity1.add_component(LifetimeComponent(time=0, max_time=5))
        
        # 查询实体
        found = em.get_entity(entity1.entity_id)
        all_entities = em.get_all_entities()
        
        # 按组件类型查询
        position_entities = em.get_entities_with_component(PositionComponent)
        
        # 更新（会自动调用 IUpdateable 组件的 update）
        em.tick(delta_time)
        
        # 销毁实体
        em.destroy_entity(entity2.entity_id)
    """

    def __init__(self):
        """
        初始化实体管理器。
        """
        self._next_entity_id: int = 1
        self._entities: Dict[int, IEntity] = {}
        self._pending_destructions: Set[int] = set()
        self._is_ticking: bool = False
        self._id_lock: Lock = Lock()
        self._entities_lock: Lock = Lock()

    def create_entity(self) -> IEntity:
        """
        创建一个新的实体。
        
        生成全局唯一的 ID，并将实体添加到活动实体集合中。
        
        返回：
            新创建的实体实例（BaseEntity）
            
        线程安全：此方法是线程安全的
        """
        with self._id_lock:
            entity_id = self._next_entity_id
            self._next_entity_id += 1
        
        entity = BaseEntity(entity_id=entity_id)
        
        with self._entities_lock:
            self._entities[entity_id] = entity
        
        return entity

    def destroy_entity(self, entity_id: int) -> bool:
        """
        销毁一个实体。
        
        如果在 Tick 执行过程中调用，销毁将延迟到当前 Tick 完成后生效。
        
        参数：
            entity_id: 要销毁的实体的 ID
            
        返回：
            True 如果实体存在并被标记为销毁；False 如果实体不存在
        """
        with self._entities_lock:
            if entity_id not in self._entities:
                return False
            
            if self._is_ticking:
                self._pending_destructions.add(entity_id)
            else:
                del self._entities[entity_id]
        
        return True

    def get_entity(self, entity_id: int) -> Optional[IEntity]:
        """
        根据 ID 获取实体。
        
        参数：
            entity_id: 要获取的实体的 ID
            
        返回：
            实体实例，如果不存在则返回 None
            
        线程安全：此方法是线程安全的
        """
        with self._entities_lock:
            return self._entities.get(entity_id)

    def get_all_entities(self) -> List[IEntity]:
        """
        获取所有活动实体的列表。
        
        返回：
            包含所有活动实体的列表（不包括待销毁的）
            
        线程安全：此方法是线程安全的
        """
        with self._entities_lock:
            return list(self._entities.values())

    def get_entities_with_component(self, component_type: Type) -> List[IEntity]:
        """
        获取拥有指定类型组件的所有实体。
        
        这是一个便利方法，用于快速查询拥有特定组件的实体。
        
        参数：
            component_type: 要查询的组件类型
            
        返回：
            包含该类型组件的所有实体列表
        """
        result: List[IEntity] = []
        with self._entities_lock:
            for entity in self._entities.values():
                if entity.has_component(component_type):
                    result.append(entity)
        return result

    def has_entity(self, entity_id: int) -> bool:
        """
        检查指定 ID 的实体是否存在。
        
        参数：
            entity_id: 要检查的实体 ID
            
        返回：
            True 如果实体存在且处于活动状态；否则返回 False
        """
        with self._entities_lock:
            return entity_id in self._entities and entity_id not in self._pending_destructions

    def get_entity_count(self) -> int:
        """
        获取当前活动实体的数量。
        
        返回：
            活动实体的数量（不包括待销毁的）
        """
        with self._entities_lock:
            return len(self._entities) - len(self._pending_destructions)

    def tick(self, delta: float) -> None:
        """
        执行一帧的更新。
        
        这是 ITickable 接口的实现，会被 GameLoopManager 每帧调用。
        
        更新过程：
        1. 遍历所有活动实体
        2. 对每个实体，遍历其所有组件
        3. 如果组件实现了 IUpdateable 接口，调用其 update 方法
        4. 处理待销毁的实体
        
        参数：
            delta: 自上一帧以来经过的时间（秒），应为非负值
        """
        if delta < 0:
            delta = 0.0
        
        self._is_ticking = True
        
        with self._entities_lock:
            entities_to_process = list(self._entities.items())
        
        for entity_id, entity in entities_to_process:
            if entity_id in self._pending_destructions:
                continue
            
            for component in entity.get_components():
                if isinstance(component, IUpdateable):
                    component.update(delta)
        
        self._is_ticking = False
        self._process_pending_destructions()

    def _process_pending_destructions(self) -> None:
        """
        处理待销毁的实体。
        
        在 Tick 完成后调用，实际删除所有待销毁的实体。
        """
        with self._entities_lock:
            for entity_id in self._pending_destructions:
                if entity_id in self._entities:
                    del self._entities[entity_id]
            self._pending_destructions.clear()

    def clear_all_entities(self) -> None:
        """
        清除所有实体。
        
        如果在 Tick 执行过程中调用，清除将延迟到当前 Tick 完成后生效。
        """
        with self._entities_lock:
            if self._is_ticking:
                self._pending_destructions.update(self._entities.keys())
            else:
                self._entities.clear()
                self._pending_destructions.clear()

    def reset(self) -> None:
        """
        重置实体管理器。
        
        清除所有实体并重置 ID 计数器。
        注意：此方法不应该在 Tick 过程中调用。
        """
        with self._id_lock:
            self._next_entity_id = 1
        
        with self._entities_lock:
            self._entities.clear()
            self._pending_destructions.clear()
