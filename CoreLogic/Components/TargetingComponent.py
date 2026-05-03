"""
索敌组件

TargetingComponent 用于赋予实体（如防御塔）"视觉"能力，
能够自动扫描并锁定范围内的敌人。

============================================================================
【架构说明】
============================================================================

此组件实现了 IUpdateable 接口，用于自动索敌逻辑。
与 MovementComponent 类似，这是一个有意识的设计选择，
用于简化防御塔的索敌逻辑。

使用方式：
    transform = TransformComponent(x=5.0, y=3.0)
    targeting = TargetingComponent(
        search_radius=3.0,
        transform=transform,
        entity_id=tower_entity.entity_id,
    )
    entity.add_component(transform)
    entity.add_component(targeting)

    # EntityManager.tick 会自动调用 targeting.update(delta)
    # targeting.current_target_id 会自动更新为最近的敌人 ID
============================================================================
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, List

from CoreLogic.Interfaces.IUpdateable import IUpdateable
from CoreLogic.Components.TransformComponent import TransformComponent
from CoreLogic.Components.HealthComponent import HealthComponent
from CoreLogic.Managers.EntityManager import EntityManager
from CoreLogic.Managers.InsanityManager import InsanityManager
from CoreLogic.Core.ServiceLocator import try_get_service
from CoreLogic.Interfaces.IGameLogger import IGameLogger


@dataclass
class TargetingComponent(IUpdateable):
    """
    索敌组件，赋予实体自动扫描并锁定敌人的能力。
    
    此组件实现了 IUpdateable 接口，需要与 TransformComponent 配合使用。
    EntityManager.tick 会自动调用 update 方法，扫描范围内的敌人并锁定最近的目标。
    
    属性：
        search_radius: 索敌半径（单位：格），敌人在此范围内会被检测到
        current_target_id: 当前锁定的敌人 Entity ID，没有目标时为 None
        transform: 关联的 TransformComponent 引用，用于获取自身位置
        entity_id: 所属实体的 ID，用于在索敌时排除自己
        _last_scan_time: 私有标记，记录上次扫描的时间（用于控制扫描频率）
        _scan_interval: 扫描间隔（秒），默认 0.1 秒扫描一次，避免每帧都扫描
    
    使用示例：
        # 创建防御塔实体
        tower = entity_manager.create_entity()
        tower_transform = TransformComponent(x=5.0, y=3.0)
        tower.add_component(tower_transform)
        tower.add_component(TargetingComponent(
            search_radius=3.0,
            transform=tower_transform,
            entity_id=tower.entity_id,
        ))
        
        # 创建敌人实体（带 HealthComponent 和 TransformComponent）
        enemy = entity_manager.create_entity()
        enemy.add_component(TransformComponent(x=6.0, y=3.0))
        enemy.add_component(HealthComponent(current_health=100, max_health=100))
        
        # 每帧更新后，current_target_id 会自动设置为敌人的 ID
        entity_manager.tick(delta=0.1)
        targeting = tower.get_component(TargetingComponent)
        print(targeting.current_target_id)  # 输出敌人的 ID
    """
    
    search_radius: float = 1.0
    current_target_id: Optional[int] = None
    transform: Optional[TransformComponent] = None
    entity_id: Optional[int] = None
    _scan_interval: float = 0.1
    _last_scan_time: float = field(default=0.0, repr=False)
    _accumulated_time: float = field(default=0.0, repr=False)
    
    @property
    def has_target(self) -> bool:
        """
        是否有锁定的目标。
        
        返回：
            True 如果 current_target_id 不为 None
        """
        return self.current_target_id is not None
    
    def clear_target(self) -> None:
        """
        清除当前锁定的目标。
        """
        self.current_target_id = None
    
    def update(self, delta: float) -> None:
        """
        每帧更新方法，实现 IUpdateable 接口。
        
        由 EntityManager.tick 自动调用。
        
        索敌逻辑：
        1. 如果没有 transform 引用或 search_radius <= 0，直接返回
        2. 控制扫描频率，避免每帧都扫描
        3. 通过 EntityManager 获取所有带 HealthComponent 的实体
        4. 对每个实体检查是否有 TransformComponent
        5. 排除自己（通过 entity_id 比较）
        6. 计算与每个敌人的距离
        7. 筛选出距离小于 search_radius 的敌人
        8. 选择距离最近的敌人，更新 current_target_id
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
        """
        if self.transform is None:
            return
        
        if self.search_radius <= 0.0:
            self.clear_target()
            return
        
        self._accumulated_time += delta
        if self._accumulated_time < self._scan_interval:
            return
        
        self._accumulated_time = 0.0
        self._last_scan_time += self._scan_interval
        
        entity_manager = try_get_service(EntityManager)
        if entity_manager is None:
            return
        
        self._perform_search(entity_manager)
    
    def _get_insanity_manager(self) -> Optional[InsanityManager]:
        """
        获取疯狂值管理器服务。
        
        返回：
            InsanityManager 实例，如果未注册则返回 None
        """
        return try_get_service(InsanityManager)
    
    def _get_effective_search_radius(self) -> float:
        """
        获取当前有效的索敌半径。
        
        在高疯狂状态下，索敌距离减半（高风险高回报机制）。
        
        返回：
            有效的索敌半径
        """
        base_radius = self.search_radius
        
        insanity_manager = self._get_insanity_manager()
        if insanity_manager is not None and insanity_manager.is_high_insanity():
            multiplier = insanity_manager.high_insanity_search_radius_multiplier
            return base_radius * multiplier
        
        return base_radius
    
    def _perform_search(self, entity_manager: EntityManager) -> None:
        """
        执行索敌逻辑。
        
        在高疯狂状态下，索敌距离会减半（高风险高回报机制）。
        
        参数：
            entity_manager: EntityManager 实例，用于查询实体
        """
        if self.transform is None:
            return
        
        my_x = self.transform.x
        my_y = self.transform.y
        
        effective_radius = self._get_effective_search_radius()
        search_radius_squared = effective_radius * effective_radius
        
        candidates: List[Tuple[int, float]] = []
        
        health_entities = entity_manager.get_entities_with_component(HealthComponent)
        
        for entity in health_entities:
            if self.entity_id is not None and entity.entity_id == self.entity_id:
                continue
            
            transform = entity.get_component(TransformComponent)
            if transform is None:
                continue
            
            dx = transform.x - my_x
            dy = transform.y - my_y
            distance_squared = dx * dx + dy * dy
            
            if distance_squared <= search_radius_squared:
                candidates.append((entity.entity_id, distance_squared))
        
        if not candidates:
            self.clear_target()
            return
        
        candidates.sort(key=lambda x: x[1])
        closest_id, _ = candidates[0]
        self.current_target_id = closest_id
