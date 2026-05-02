"""
状态效果组件

BuffComponent 用于管理实体上的状态效果列表。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯粹的数据容器，不包含任何业务逻辑。
所有状态效果相关的逻辑（如每帧更新、应用效果）都应该在 BuffSystem 中实现。

BuffComponent 存储：
- 活动状态效果列表
- 提供添加、移除、查询效果的方法

与 StatusEffect 的关系：
- BuffComponent: 数据容器，存储状态效果列表
- StatusEffect: 包含数据和逻辑的状态效果实例
- BuffSystem: 业务逻辑，处理每帧更新和效果应用

使用方式：
    # 为实体添加 BuffComponent
    entity.add_component(BuffComponent())
    
    # 添加状态效果
    buff_comp = entity.get_component(BuffComponent)
    buff_comp.add_effect(PoisonEffect(duration=5.0, damage_percent=0.05))
    
    # BuffSystem 会自动处理每帧更新
============================================================================
"""

from dataclasses import dataclass, field
from typing import List, Optional, Type, TypeVar

from CoreLogic.StatusEffects.StatusEffect import StatusEffect


T = TypeVar('T', bound=StatusEffect)


@dataclass
class BuffComponent:
    """
    状态效果组件，管理实体上的状态效果列表。
    
    存储活动状态效果列表，提供添加、移除、查询效果的方法。
    这是一个纯粹的数据容器，所有业务逻辑由 BuffSystem 处理。
    
    属性：
        active_effects: 活动状态效果列表
        
    使用示例：
        # 为敌人添加 BuffComponent
        enemy_entity.add_component(BuffComponent())
        
        # 获取组件并添加状态效果
        buff_comp = enemy_entity.get_component(BuffComponent)
        buff_comp.add_effect(PoisonEffect(duration=5.0, damage_percent=0.05))
        
        # 检查是否有特定类型的效果
        if buff_comp.has_effect(PoisonEffect):
            print("敌人已中毒")
    """
    
    active_effects: List[StatusEffect] = field(default_factory=list)
    
    def add_effect(self, effect: StatusEffect) -> None:
        """
        添加状态效果。
        
        如果相同类型的效果已存在，默认行为是刷新持续时间。
        子类可以重写此方法实现不同的叠加逻辑。
        
        参数：
            effect: 要添加的状态效果实例
        """
        existing_effect = self.get_effect(type(effect))
        
        if existing_effect is not None:
            existing_effect.refresh_duration()
        else:
            self.active_effects.append(effect)
    
    def remove_effect(self, effect: StatusEffect) -> None:
        """
        移除指定的状态效果。
        
        参数：
            effect: 要移除的状态效果实例
        """
        if effect in self.active_effects:
            self.active_effects.remove(effect)
    
    def remove_effect_by_type(self, effect_type: Type[T]) -> Optional[T]:
        """
        移除指定类型的第一个状态效果。
        
        参数：
            effect_type: 要移除的状态效果类型
            
        返回：
            被移除的效果实例，如果不存在则返回 None
        """
        for i, effect in enumerate(self.active_effects):
            if isinstance(effect, effect_type):
                return self.active_effects.pop(i)
        return None
    
    def remove_all_effects(self) -> None:
        """
        移除所有状态效果。
        """
        self.active_effects.clear()
    
    def get_effect(self, effect_type: Type[T]) -> Optional[T]:
        """
        获取指定类型的第一个状态效果。
        
        参数：
            effect_type: 状态效果类型
            
        返回：
            第一个匹配的效果实例，如果不存在则返回 None
        """
        for effect in self.active_effects:
            if isinstance(effect, effect_type):
                return effect
        return None
    
    def get_all_effects(self, effect_type: Type[T]) -> List[T]:
        """
        获取指定类型的所有状态效果。
        
        参数：
            effect_type: 状态效果类型
            
        返回：
            所有匹配的效果实例列表
        """
        return [effect for effect in self.active_effects if isinstance(effect, effect_type)]
    
    def has_effect(self, effect_type: Type[StatusEffect]) -> bool:
        """
        检查是否存在指定类型的状态效果。
        
        参数：
            effect_type: 状态效果类型
            
        返回：
            True 如果存在该类型的效果
        """
        return self.get_effect(effect_type) is not None
    
    def get_effect_count(self) -> int:
        """
        获取活动状态效果的数量。
        
        返回：
            活动效果的数量
        """
        return len(self.active_effects)
    
    def remove_expired_effects(self) -> List[StatusEffect]:
        """
        移除所有已过期的状态效果。
        
        返回：
            被移除的过期效果列表
        """
        expired_effects = [effect for effect in self.active_effects if effect.is_expired]
        
        for effect in expired_effects:
            self.active_effects.remove(effect)
        
        return expired_effects
