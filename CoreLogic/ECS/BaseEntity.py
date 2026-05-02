"""
基础实体实现类

BaseEntity 是 IEntity 接口的基础实现，内部使用字典来存储和管理装载的 Component。

============================================================================
【架构规范强制声明】
============================================================================

BaseEntity 是一个纯粹的数据容器实现，不包含任何游戏业务逻辑。
所有业务逻辑都应该在 System 中实现，通过查询和操作 Entity 的 Component 来完成。

BaseEntity 的职责仅限于：
1. 存储和管理全局唯一的 entity_id
2. 使用字典存储和管理 Component 实例
3. 实现 IEntity 接口定义的组件操作方法

扩展说明：
- 如果你需要特殊的组件管理逻辑，可以继承 BaseEntity 或重新实现 IEntity 接口
- 但请确保任何子类都不包含业务逻辑
============================================================================
"""

from typing import Dict, Type, Optional, TypeVar, List

from CoreLogic.Interfaces.IComponent import IComponent
from CoreLogic.Interfaces.IEntity import IEntity

T = TypeVar('T', bound=IComponent)


class BaseEntity(IEntity):
    """
    基础实体实现类。
    
    内部使用字典（以组件类型为键）来存储和管理 Component 实例。
    这是一个纯粹的数据容器实现，不包含任何游戏业务逻辑。
    
    组件存储策略：
    - 每个类型的组件最多只能有一个实例
    - 添加相同类型的组件会覆盖已存在的组件
    - 组件类型作为字典的键，组件实例作为值
    
    使用示例：
        # 创建实体
        entity = BaseEntity(entity_id=1)
        
        # 添加组件
        entity.add_component(PositionComponent(x=10, y=20))
        entity.add_component(HealthComponent(current=100, max=100))
        
        # 获取组件
        pos = entity.get_component(PositionComponent)
        if pos:
            print(f"Position: ({pos.x}, {pos.y})")
        
        # 检查组件是否存在
        if entity.has_component(HealthComponent):
            print("Entity has health component")
        
        # 移除组件
        entity.remove_component(HealthComponent)
    """

    def __init__(self, entity_id: int):
        """
        初始化基础实体。
        
        参数：
            entity_id: 实体的全局唯一标识符
        """
        self._entity_id: int = entity_id
        self._components: Dict[Type[IComponent], IComponent] = {}

    @property
    def entity_id(self) -> int:
        """
        获取实体的全局唯一 ID。
        
        返回：
            实体的唯一标识符
        """
        return self._entity_id

    def add_component(self, component: T) -> None:
        """
        向实体添加一个组件。
        
        如果实体已经包含相同类型的组件，新组件将替换旧组件。
        
        参数：
            component: 要添加的组件实例，必须实现 IComponent 协议
        """
        component_type: Type[IComponent] = type(component)
        self._components[component_type] = component

    def get_component(self, component_type: Type[T]) -> Optional[T]:
        """
        从实体获取指定类型的组件。
        
        参数：
            component_type: 要获取的组件类型
        
        返回：
            如果实体包含该类型的组件，返回组件实例；否则返回 None
        """
        return self._components.get(component_type)

    def remove_component(self, component_type: Type[T]) -> bool:
        """
        从实体移除指定类型的组件。
        
        参数：
            component_type: 要移除的组件类型
        
        返回：
            如果成功移除组件返回 True；如果实体不包含该类型的组件返回 False
        """
        if component_type in self._components:
            del self._components[component_type]
            return True
        return False

    def has_component(self, component_type: Type[T]) -> bool:
        """
        检查实体是否包含指定类型的组件。
        
        参数：
            component_type: 要检查的组件类型
        
        返回：
            如果实体包含该类型的组件返回 True；否则返回 False
        """
        return component_type in self._components

    def get_components(self) -> List[IComponent]:
        """
        获取当前实体持有的所有组件列表。
        
        返回：
            包含所有组件实例的列表。如果实体没有任何组件，返回空列表。
        """
        return list(self._components.values())
