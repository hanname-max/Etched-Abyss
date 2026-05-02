"""
单发攻击策略

SingleShotStrategy 实现默认的单发攻击行为，
只向锁定的主目标发射一个投射物。

============================================================================
【策略模式说明】
============================================================================

这是 Concrete Strategy（具体策略）的实现，
封装了默认的单发攻击算法。

与 IAttackStrategy 接口的关系：
- 实现 execute_fire 方法，定义单发攻击逻辑
- 实现 strategy_id 属性，返回 "single_shot"

使用场景：
- 防御塔的默认攻击行为
- 当没有装备特殊攻击器官时使用
============================================================================
"""

from typing import Any, List, Optional

from CoreLogic.Interfaces.IAttackStrategy import IAttackStrategy
from CoreLogic.Components.TransformComponent import TransformComponent
from CoreLogic.Events.TowerFiredEvent import TowerFiredEvent
from CoreLogic.Core.EventBus import publish
from CoreLogic.StatusEffects.StatusEffect import StatusEffect


class SingleShotStrategy(IAttackStrategy):
    """
    单发攻击策略。
    
    默认攻击策略，只向锁定的主目标发射一个投射物。
    这是所有防御塔的默认攻击行为。
    
    属性：
        strategy_id: 策略标识符，固定为 "single_shot"
        projectile_speed: 投射物飞行速度（单位/秒）
    
    使用示例：
        # 创建单发策略
        strategy = SingleShotStrategy(projectile_speed=8.0)
        
        # 执行攻击（由 AttackSystem 调用）
        projectile_count = strategy.execute_fire(
            tower_entity=tower,
            primary_target_id=enemy_id,
            damage=25.0,
            status_effects=[]
        )
        print(f"发射了 {projectile_count} 个投射物")  # 输出 1
    """
    
    _projectile_speed: float = 8.0
    
    def __init__(self, projectile_speed: float = 8.0) -> None:
        """
        初始化单发攻击策略。
        
        参数：
            projectile_speed: 投射物飞行速度（单位/秒），默认为 8.0
        """
        self._projectile_speed = projectile_speed
    
    @property
    def strategy_id(self) -> str:
        """
        获取策略标识符。
        
        返回：
            "single_shot"，标识这是单发攻击策略
        """
        return "single_shot"
    
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
    
    def execute_fire(
        self,
        tower_entity: Any,
        primary_target_id: int,
        damage: float,
        status_effects: Optional[List[StatusEffect]] = None
    ) -> int:
        """
        执行单发攻击。
        
        向锁定的主目标发射一个投射物：
        1. 从防御塔实体获取 TransformComponent 以获得发射位置
        2. 创建并发布 TowerFiredEvent
        3. ProjectileSystem 会监听此事件并创建投射物实体
        
        参数：
            tower_entity: 防御塔实体，必须有 TransformComponent
            primary_target_id: 主目标的实体 ID
            damage: 投射物的伤害值
            status_effects: 可选的状态效果列表
            
        返回：
            发射的投射物数量（始终为 1）
            
        异常：
            ValueError: 如果 tower_entity 没有 TransformComponent
        """
        if tower_entity is None:
            return 0
        
        transform = tower_entity.get_component(TransformComponent)
        if transform is None:
            return 0
        
        tower_id = tower_entity.entity_id
        
        effects = status_effects if status_effects is not None else []
        
        event = TowerFiredEvent(
            tower_id=tower_id,
            target_id=primary_target_id,
            damage=damage,
            start_x=transform.x,
            start_y=transform.y,
            speed=self._projectile_speed,
            status_effects=effects
        )
        
        publish(event)
        
        return 1
