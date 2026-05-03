"""
攻城状态组件

SiegeComponent 用于记录敌人在攻城状态下的数据。
当敌人路径被彻底堵死时，进入攻城状态，开始攻击阻挡它的防御塔。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯粹的数据容器，不包含任何业务逻辑。
所有攻城状态相关的逻辑（如寻找目标、移动、攻击）都应该在 System 中实现。

使用 SiegeSystem 来处理：
- 寻找最近的阻挡防御塔
- 向防御塔移动
- 周期性攻击防御塔
- 塔被摧毁后重新寻路
============================================================================
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class SiegeComponent:
    """
    攻城状态组件，记录敌人在攻城状态下的数据。
    
    当敌人的路径被彻底堵死（Pathfinder 返回空队列）时，
    敌人会进入攻城状态，开始攻击阻挡它的防御塔。
    
    属性：
        target_tower_id: 当前攻击的目标防御塔实体 ID
        target_tower_grid: 目标塔的网格坐标 (x, y)
        attack_damage: 每次攻击造成的伤害
        attack_interval: 攻击间隔时间（秒）
        cooldown_remaining: 剩余冷却时间
        destination_x: 原始终点 X 坐标（塔被摧毁后需要重寻路）
        destination_y: 原始终点 Y 坐标（塔被摧毁后需要重寻路）
        _is_active: 私有标记，表示攻城状态是否激活
        
    使用示例：
        # 敌人进入攻城状态
        siege = SiegeComponent(
            target_tower_id=tower.entity_id,
            target_tower_grid=(5, 3),
            attack_damage=10.0,
            attack_interval=1.0,
            destination_x=10.0,
            destination_y=0.0
        )
        enemy.add_component(siege)
        
        # SiegeSystem 会每帧更新攻城状态
    """
    
    target_tower_id: Optional[int] = None
    target_tower_grid: Optional[Tuple[int, int]] = None
    attack_damage: float = 10.0
    attack_interval: float = 1.0
    cooldown_remaining: float = 0.0
    destination_x: float = 0.0
    destination_y: float = 0.0
    _is_active: bool = field(default=False, repr=False)
    
    @property
    def is_active(self) -> bool:
        """
        攻城状态是否激活。
        
        返回：
            True 如果敌人处于攻城状态
        """
        return self._is_active
    
    @property
    def has_target(self) -> bool:
        """
        是否有攻击目标。
        
        返回：
            True 如果 target_tower_id 不为 None
        """
        return self.target_tower_id is not None
    
    @property
    def is_ready(self) -> bool:
        """
        攻击是否准备就绪（冷却已完成）。
        
        返回：
            True 如果 cooldown_remaining <= 0
        """
        return self.cooldown_remaining <= 0.0
    
    def activate(
        self,
        target_tower_id: int,
        target_tower_grid: Tuple[int, int],
        attack_damage: float,
        attack_interval: float,
        destination_x: float,
        destination_y: float,
    ) -> None:
        """
        激活攻城状态。
        
        参数：
            target_tower_id: 目标防御塔的实体 ID
            target_tower_grid: 目标塔的网格坐标 (x, y)
            attack_damage: 每次攻击造成的伤害
            attack_interval: 攻击间隔时间（秒）
            destination_x: 原始终点 X 坐标
            destination_y: 原始终点 Y 坐标
        """
        self.target_tower_id = target_tower_id
        self.target_tower_grid = target_tower_grid
        self.attack_damage = attack_damage
        self.attack_interval = attack_interval
        self.cooldown_remaining = 0.0
        self.destination_x = destination_x
        self.destination_y = destination_y
        self._is_active = True
    
    def deactivate(self) -> None:
        """
        取消攻城状态。
        
        当防御塔被摧毁或敌人找到新路径时调用。
        """
        self.target_tower_id = None
        self.target_tower_grid = None
        self.cooldown_remaining = 0.0
        self._is_active = False
    
    def update_cooldown(self, delta: float) -> None:
        """
        更新冷却时间。
        
        由 SiegeSystem 每帧调用，减少剩余冷却时间。
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
        """
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= delta
            if self.cooldown_remaining < 0:
                self.cooldown_remaining = 0.0
    
    def start_cooldown(self) -> None:
        """
        开始新的冷却周期。
        
        攻击完成后调用，设置下一次攻击的冷却时间。
        """
        if self.attack_interval > 0:
            self.cooldown_remaining = self.attack_interval
