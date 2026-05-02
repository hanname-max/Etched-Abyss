"""
实体接口定义

IEntity 是所有实体的基接口。
一个 Entity 在逻辑上就是一个由全局唯一 ID 和一组 Component 组成的容器。

============================================================================
【架构规范强制声明】
============================================================================

Entity 是一个纯粹的标识符 + 组件容器，不包含任何业务逻辑。
所有对 Entity 的操作都应该通过 System 来完成，而不是在 Entity 类中定义方法。

Entity 的唯一职责是：
1. 拥有一个全局唯一的标识符
2. 管理一组 Component 的添加、获取、移除和查询

正确示例：
    entity = world.create_entity()
    entity.add_component(PositionComponent(x=0, y=0))
    entity.add_component(VelocityComponent(vx=1, vy=0))
    
    # 在 System 中处理逻辑
    for entity in world.query(PositionComponent, VelocityComponent):
        pos = entity.get_component(PositionComponent)
        vel = entity.get_component(VelocityComponent)
        pos.x += vel.vx * delta

错误示例（严禁使用）：
    # Entity 中包含业务逻辑
    class PlayerEntity(IEntity):
        def move(self, dx, dy):  # 这是业务逻辑，不应该在 Entity 中
            pos = self.get_component(PositionComponent)
            pos.x += dx
            pos.y += dy
============================================================================
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Optional, Type, List

from CoreLogic.Interfaces.IComponent import IComponent

T = TypeVar('T', bound=IComponent)


class IEntity(ABC):
    """
    实体基接口。
    
    一个 Entity 在逻辑上就是一个由全局唯一 ID 和一组 Component 组成的容器。
    Entity 是纯粹的数据容器，不包含任何业务逻辑。
    
    核心特性：
    1. 拥有全局唯一的 ID 标识符
    2. 可以添加、获取、移除和查询 Component
    3. 不包含任何业务逻辑
    
    使用示例：
        # 创建实体并添加组件
        entity = BaseEntity(entity_id=1)
        entity.add_component(PositionComponent(x=10, y=20))
        entity.add_component(HealthComponent(current=100, max=100))
        
        # 查询组件
        if entity.has_component(PositionComponent):
            pos = entity.get_component(PositionComponent)
            print(f"Position: ({pos.x}, {pos.y})")
        
        # 移除组件
        entity.remove_component(HealthComponent)
    """

    @property
    @abstractmethod
    def entity_id(self) -> int:
        """
        获取实体的全局唯一 ID。
        
        返回：
            实体的唯一标识符
        """
        pass

    @abstractmethod
    def add_component(self, component: T) -> None:
        """
        向实体添加一个组件。
        
        如果实体已经包含相同类型的组件，新组件将替换旧组件。
        
        参数：
            component: 要添加的组件实例，必须实现 IComponent 协议
        
        示例：
            entity.add_component(PositionComponent(x=0, y=0))
        """
        pass

    @abstractmethod
    def get_component(self, component_type: Type[T]) -> Optional[T]:
        """
        从实体获取指定类型的组件。
        
        参数：
            component_type: 要获取的组件类型
        
        返回：
            如果实体包含该类型的组件，返回组件实例；否则返回 None
        
        示例：
            pos = entity.get_component(PositionComponent)
            if pos:
                print(f"x: {pos.x}, y: {pos.y}")
        """
        pass

    @abstractmethod
    def remove_component(self, component_type: Type[T]) -> bool:
        """
        从实体移除指定类型的组件。
        
        参数：
            component_type: 要移除的组件类型
        
        返回：
            如果成功移除组件返回 True；如果实体不包含该类型的组件返回 False
        
        示例：
            entity.remove_component(HealthComponent)
        """
        pass

    @abstractmethod
    def has_component(self, component_type: Type[T]) -> bool:
        """
        检查实体是否包含指定类型的组件。
        
        参数：
            component_type: 要检查的组件类型
        
        返回：
            如果实体包含该类型的组件返回 True；否则返回 False
        
        示例：
            if entity.has_component(PositionComponent):
                # 处理拥有位置组件的实体
                pass
        """
        pass

    @abstractmethod
    def get_components(self) -> List[IComponent]:
        """
        获取当前实体持有的所有组件列表。
        
        返回：
            包含所有组件实例的列表。如果实体没有任何组件，返回空列表。
        
        示例：
            components = entity.get_components()
            for component in components:
                print(type(component).__name__)
        """
        pass
