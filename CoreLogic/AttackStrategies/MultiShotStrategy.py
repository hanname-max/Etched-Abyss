"""
多发攻击策略

MultiShotStrategy 实现多目标分裂攻击行为，
向主目标及周围半径内的额外敌人同时发射投射物。

============================================================================
【策略模式说明】
============================================================================

这是 Concrete Strategy（具体策略）的实现，
封装了多目标分裂攻击算法。

与 IAttackStrategy 接口的关系：
- 实现 execute_fire 方法，定义多目标攻击逻辑
- 实现 strategy_id 属性，返回 "multi_shot"

触发条件：
- 装备"分裂神经"器官时激活此策略
- 器官卸下时恢复默认的 SingleShotStrategy

攻击逻辑：
1. 向锁定的主目标发射投射物
2. 查找主目标周围 radius 范围内的其他敌人
3. 向最多 max_additional_targets 个额外敌人发射投射物
4. 每个投射物独立计算伤害
============================================================================
"""

from typing import Any, List, Optional, Tuple

from CoreLogic.Interfaces.IAttackStrategy import IAttackStrategy
from CoreLogic.Components.TransformComponent import TransformComponent
from CoreLogic.Components.HealthComponent import HealthComponent
from CoreLogic.Events.TowerFiredEvent import TowerFiredEvent
from CoreLogic.Core.EventBus import publish
from CoreLogic.Core.ServiceLocator import try_get_service
from CoreLogic.Managers.EntityManager import EntityManager
from CoreLogic.StatusEffects.StatusEffect import StatusEffect


class MultiShotStrategy(IAttackStrategy):
    """
    多发攻击策略（分裂攻击）。
    
    特殊攻击策略，向主目标及周围额外敌人同时发射投射物。
    由"分裂神经"器官触发。
    
    属性：
        strategy_id: 策略标识符，固定为 "multi_shot"
        projectile_speed: 投射物飞行速度（单位/秒）
        split_radius: 分裂攻击的搜索半径（单位：格）
        max_additional_targets: 最多攻击的额外目标数量
        
    使用示例：
        # 创建多发策略（分裂神经效果）
        strategy = MultiShotStrategy(
            projectile_speed=8.0,
            split_radius=2.0,
            max_additional_targets=2
        )
        
        # 执行攻击（由 AttackSystem 调用）
        projectile_count = strategy.execute_fire(
            tower_entity=tower,
            primary_target_id=enemy_id,
            damage=25.0,
            status_effects=[]
        )
        # 最多发射 3 个投射物（1 主目标 + 2 额外目标）
    """
    
    _projectile_speed: float = 8.0
    _split_radius: float = 2.0
    _max_additional_targets: int = 2
    
    def __init__(
        self,
        projectile_speed: float = 8.0,
        split_radius: float = 2.0,
        max_additional_targets: int = 2
    ) -> None:
        """
        初始化多发攻击策略。
        
        参数：
            projectile_speed: 投射物飞行速度（单位/秒），默认为 8.0
            split_radius: 分裂攻击的搜索半径（单位：格），默认为 2.0
            max_additional_targets: 最多攻击的额外目标数量，默认为 2
        """
        self._projectile_speed = projectile_speed
        self._split_radius = split_radius
        self._max_additional_targets = max_additional_targets
    
    @property
    def strategy_id(self) -> str:
        """
        获取策略标识符。
        
        返回：
            "multi_shot"，标识这是多发攻击策略
        """
        return "multi_shot"
    
    @property
    def projectile_speed(self) -> float:
        """
        获取投射物飞行速度。
        
        返回：
            投射物飞行速度（单位/秒）
        """
        return self._projectile_speed
    
    @projectile_speed.setter
    def projectile_speed(self, value: float) -> None:
        """
        设置投射物飞行速度。
        
        参数：
            value: 投射物飞行速度（单位/秒）
        """
        if value > 0:
            self._projectile_speed = value
    
    @property
    def split_radius(self) -> float:
        """
        获取分裂攻击的搜索半径。
        
        返回：
            搜索半径（单位：格）
        """
        return self._split_radius
    
    @split_radius.setter
    def split_radius(self, value: float) -> None:
        """
        设置分裂攻击的搜索半径。
        
        参数：
            value: 搜索半径（单位：格）
        """
        if value >= 0:
            self._split_radius = value
    
    @property
    def max_additional_targets(self) -> int:
        """
        获取最多攻击的额外目标数量。
        
        返回：
            额外目标数量
        """
        return self._max_additional_targets
    
    @max_additional_targets.setter
    def max_additional_targets(self, value: int) -> None:
        """
        设置最多攻击的额外目标数量。
        
        参数：
            value: 额外目标数量
        """
        if value >= 0:
            self._max_additional_targets = value
    
    def execute_fire(
        self,
        tower_entity: Any,
        primary_target_id: int,
        damage: float,
        status_effects: Optional[List[StatusEffect]] = None
    ) -> int:
        """
        执行多发攻击（分裂攻击）。
        
        攻击逻辑：
        1. 向锁定的主目标发射投射物
        2. 获取主目标的位置
        3. 在主目标周围 split_radius 范围内搜索其他敌人
        4. 排除主目标和防御塔自身
        5. 按距离排序，选择最近的 max_additional_targets 个敌人
        6. 向每个选中的额外目标发射独立的投射物
        
        每个投射物：
        - 独立计算伤害
        - 独立飞行轨迹
        - 独立的命中判定
        
        参数：
            tower_entity: 防御塔实体，必须有 TransformComponent
            primary_target_id: 主目标的实体 ID
            damage: 每个投射物的基础伤害值
            status_effects: 可选的状态效果列表
            
        返回：
            实际发射的投射物数量（1 + 额外目标数）
        """
        if tower_entity is None:
            return 0
        
        tower_transform = tower_entity.get_component(TransformComponent)
        if tower_transform is None:
            return 0
        
        tower_id = tower_entity.entity_id
        effects = status_effects if status_effects is not None else []
        
        projectile_count = 0
        
        projectile_count += self._fire_at_target(
            tower_id=tower_id,
            target_id=primary_target_id,
            damage=damage,
            start_x=tower_transform.x,
            start_y=tower_transform.y,
            status_effects=effects
        )
        
        additional_targets = self._find_additional_targets(
            primary_target_id=primary_target_id,
            tower_id=tower_id
        )
        
        for target_id in additional_targets:
            projectile_count += self._fire_at_target(
                tower_id=tower_id,
                target_id=target_id,
                damage=damage,
                start_x=tower_transform.x,
                start_y=tower_transform.y,
                status_effects=effects
            )
        
        return projectile_count
    
    def _find_additional_targets(
        self,
        primary_target_id: int,
        tower_id: int
    ) -> List[int]:
        """
        查找主目标周围的额外目标。
        
        参数：
            primary_target_id: 主目标 ID（用于排除和获取位置）
            tower_id: 防御塔 ID（用于排除）
            
        返回：
            额外目标 ID 列表，最多 max_additional_targets 个
        """
        entity_manager = try_get_service(EntityManager)
        if entity_manager is None:
            return []
        
        primary_target = entity_manager.get_entity(primary_target_id)
        if primary_target is None:
            return []
        
        primary_transform = primary_target.get_component(TransformComponent)
        if primary_transform is None:
            return []
        
        primary_x = primary_transform.x
        primary_y = primary_transform.y
        radius_squared = self._split_radius * self._split_radius
        
        candidates: List[Tuple[int, float]] = []
        
        health_entities = entity_manager.get_entities_with_component(HealthComponent)
        
        for entity in health_entities:
            entity_id = entity.entity_id
            
            if entity_id == primary_target_id:
                continue
            if entity_id == tower_id:
                continue
            
            transform = entity.get_component(TransformComponent)
            if transform is None:
                continue

            health = entity.get_component(HealthComponent)
            if health is None or health.current_health <= 0:
                continue
            
            dx = transform.x - primary_x
            dy = transform.y - primary_y
            distance_squared = dx * dx + dy * dy
            
            if distance_squared <= radius_squared:
                candidates.append((entity_id, distance_squared))
        
        candidates.sort(key=lambda x: x[1])
        
        result = [entity_id for entity_id, _ in candidates[:self._max_additional_targets]]
        
        return result
    
    def _fire_at_target(
        self,
        tower_id: int,
        target_id: int,
        damage: float,
        start_x: float,
        start_y: float,
        status_effects: List[StatusEffect]
    ) -> int:
        """
        向单个目标发射投射物。
        
        参数：
            tower_id: 防御塔 ID
            target_id: 目标 ID
            damage: 伤害值
            start_x: 发射起始 X 坐标
            start_y: 发射起始 Y 坐标
            status_effects: 状态效果列表
            
        返回：
            1（表示发射了一个投射物）
        """
        event = TowerFiredEvent(
            tower_id=tower_id,
            target_id=target_id,
            damage=damage,
            start_x=start_x,
            start_y=start_y,
            speed=self._projectile_speed,
            status_effects=status_effects.copy() if status_effects else []
        )
        
        publish(event)
        
        return 1
