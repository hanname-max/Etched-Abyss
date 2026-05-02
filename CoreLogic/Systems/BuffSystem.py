"""
状态效果系统

BuffSystem 负责处理所有实体上的状态效果的每帧更新。

============================================================================
【架构规范强制声明】
============================================================================

这是一个每帧更新的系统，实现了 ITickable 接口。
负责：
1. 查询所有拥有 BuffComponent 的实体
2. 每帧更新所有活动的状态效果
3. 移除已过期的状态效果
4. 处理状态效果的生命周期回调

与其他组件的关系：
- BuffComponent: 数据容器，存储状态效果列表
- StatusEffect: 包含数据和逻辑的状态效果实例
- BuffSystem: 业务逻辑，处理每帧更新

使用方式：
    # 初始化并启动状态效果系统
    buff_system = BuffSystem()
    buff_system.initialize()  # （可选，预留接口）
    
    # 注册到 GameLoopManager 以获得每帧更新
    loop_manager = get_service(GameLoopManager)
    loop_manager.register_tickable(buff_system)
    
    # 此时所有拥有 BuffComponent 的实体的状态效果会自动更新
    
    # 关闭时停止
    buff_system.shutdown()  # （可选，预留接口）
============================================================================
"""

from typing import Optional, List

from CoreLogic.Interfaces.ITickable import ITickable
from CoreLogic.Core.ServiceLocator import try_get_service
from CoreLogic.Managers.EntityManager import EntityManager
from CoreLogic.Components.BuffComponent import BuffComponent
from CoreLogic.StatusEffects.StatusEffect import StatusEffect
from CoreLogic.Interfaces.IGameLogger import IGameLogger


class BuffSystem(ITickable):
    """
    状态效果系统。
    
    负责处理所有实体上的状态效果的每帧更新：
    - 查询所有拥有 BuffComponent 的实体
    - 每帧更新所有活动的状态效果
    - 移除已过期的状态效果
    - 处理状态效果的生命周期回调
    
    特性：
    - 每帧更新：实现 ITickable 接口，由 GameLoopManager 调用
    - 自动清理：自动检测并移除已过期的状态效果
    - 生命周期管理：正确调用 on_apply、on_tick、on_remove 回调
    
    使用示例：
        buff_system = BuffSystem()
        
        # 注册到 GameLoopManager
        loop_manager = get_service(GameLoopManager)
        loop_manager.register_tickable(buff_system)
        
        # 此时所有状态效果会自动每帧更新
    """
    
    def __init__(self) -> None:
        """
        初始化状态效果系统。
        """
        self._is_initialized: bool = False
    
    def initialize(self) -> None:
        """
        初始化状态效果系统。
        
        预留接口，供未来扩展使用。
        """
        if self._is_initialized:
            return
        
        self._is_initialized = True
    
    def shutdown(self) -> None:
        """
        关闭状态效果系统。
        
        预留接口，供未来扩展使用。
        """
        if not self._is_initialized:
            return
        
        self._is_initialized = False
    
    def is_initialized(self) -> bool:
        """
        检查状态效果系统是否已初始化。
        
        返回：
            True 如果已初始化；否则返回 False
        """
        return self._is_initialized
    
    def _get_entity_manager(self) -> Optional[EntityManager]:
        """
        从 ServiceLocator 获取 EntityManager。
        
        返回：
            EntityManager 实例，如果未注册则返回 None
        """
        return try_get_service(EntityManager)
    
    def _get_logger(self) -> Optional[IGameLogger]:
        """
        从 ServiceLocator 获取日志器。
        
        返回：
            如果已注册，返回 IGameLogger 实例；否则返回 None
        """
        return try_get_service(IGameLogger)
    
    def _log_combat(self, message: str, **kwargs) -> None:
        """
        记录战斗日志。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数
        """
        logger = self._get_logger()
        if logger is not None:
            logger.combat(message, **kwargs)
    
    def tick(self, delta: float) -> None:
        """
        每帧更新方法，实现 ITickable 接口。
        
        由 GameLoopManager 每帧调用。
        
        更新逻辑：
        1. 从 ServiceLocator 获取 EntityManager
        2. 查询所有拥有 BuffComponent 的实体
        3. 对每个实体：
           - 获取 BuffComponent
           - 遍历所有活动状态效果
           - 调用效果的 tick 方法
           - 检查并移除已过期的效果
           - 对过期效果调用 on_remove 回调
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
        """
        if delta < 0:
            delta = 0.0
        
        entity_manager = self._get_entity_manager()
        if entity_manager is None:
            return
        
        entities = entity_manager.get_entities_with_component(BuffComponent)
        
        for entity in entities:
            buff_comp = entity.get_component(BuffComponent)
            if buff_comp is None:
                continue
            
            self._update_entity_effects(entity, buff_comp, delta)
    
    def _update_entity_effects(self, entity, buff_comp: BuffComponent, delta: float) -> None:
        """
        更新指定实体的所有状态效果。
        
        参数：
            entity: 目标实体
            buff_comp: 实体的 BuffComponent
            delta: 自上一帧以来经过的时间（秒）
        """
        effects_to_remove: List[StatusEffect] = []
        
        for effect in buff_comp.active_effects:
            if effect.is_expired:
                effects_to_remove.append(effect)
                continue
            
            effect.tick(delta, entity)
            
            if effect.is_expired:
                effects_to_remove.append(effect)
        
        for effect in effects_to_remove:
            effect.remove(entity)
            buff_comp.remove_effect(effect)
            
            self._log_combat(
                "状态效果已移除",
                entity_id=entity.entity_id,
                effect_type=type(effect).__name__,
            )
    
    def clear_all_effects(self, entity) -> None:
        """
        清除指定实体上的所有状态效果。
        
        参数：
            entity: 目标实体
        """
        buff_comp = entity.get_component(BuffComponent)
        if buff_comp is None:
            return
        
        for effect in list(buff_comp.active_effects):
            effect.remove(entity)
            buff_comp.remove_effect(effect)
            
            self._log_combat(
                "状态效果已清除",
                entity_id=entity.entity_id,
                effect_type=type(effect).__name__,
            )
    
    def get_effect_count(self, entity) -> int:
        """
        获取指定实体上的活动状态效果数量。
        
        参数：
            entity: 目标实体
            
        返回：
            活动状态效果的数量
        """
        buff_comp = entity.get_component(BuffComponent)
        if buff_comp is None:
            return 0
        
        return buff_comp.get_effect_count()
