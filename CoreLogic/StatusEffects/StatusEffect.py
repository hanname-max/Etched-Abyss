"""
状态效果基类

StatusEffect 是所有状态效果的基类，用于实现持续的效果（如中毒、减速等）。

============================================================================
【架构规范说明】
============================================================================

StatusEffect 是一个包含数据和逻辑的类，用于实现持续的效果。
与 Component 不同，StatusEffect 包含自己的更新逻辑。

核心特性：
1. 时间管理：持续时间、剩余时间、是否过期
2. 每帧更新：实现 tick 方法处理每帧逻辑
3. 生命周期回调：on_apply、on_remove、on_tick

使用方式：
    # 创建状态效果
    poison = PoisonEffect(duration=5.0, damage_percent=0.05)
    
    # 应用到目标
    poison.on_apply(target_entity)
    
    # 每帧更新
    poison.tick(delta)
    
    # 检查是否过期
    if poison.is_expired:
        poison.on_remove(target_entity)
============================================================================
"""

from abc import ABC, abstractmethod
from typing import Optional


class StatusEffect(ABC):
    """
    状态效果基类。
    
    所有持续效果（如中毒、减速、灼烧等）都应该继承此类。
    StatusEffect 包含时间管理和生命周期回调。
    
    属性：
        duration: 总持续时间（秒）
        remaining_time: 剩余持续时间（秒）
        is_expired: 是否过期
        
    使用示例：
        class MyEffect(StatusEffect):
            def __init__(self, duration: float):
                super().__init__(duration)
            
            def tick(self, delta: float, target) -> None:
                # 处理每帧逻辑
                pass
        
        # 创建效果
        effect = MyEffect(duration=5.0)
        
        # 应用效果
        effect.on_apply(target)
        
        # 每帧更新
        effect.tick(delta, target)
        
        # 移除效果
        if effect.is_expired:
            effect.on_remove(target)
    """
    
    def __init__(self, duration: float) -> None:
        """
        初始化状态效果。
        
        参数：
            duration: 总持续时间（秒）
        """
        self.duration: float = max(0.0, duration)
        self.remaining_time: float = self.duration
        self._is_applied: bool = False
    
    @property
    def is_expired(self) -> bool:
        """
        检查效果是否已过期。
        
        返回：
            True 如果剩余时间 <= 0
        """
        return self.remaining_time <= 0.0
    
    @property
    def is_applied(self) -> bool:
        """
        检查效果是否已应用。
        
        返回：
            True 如果 on_apply 已被调用
        """
        return self._is_applied
    
    def tick(self, delta: float, target) -> None:
        """
        每帧更新方法。
        
        默认实现：减少剩余时间，调用 on_tick 回调。
        子类可以重写此方法实现自定义逻辑。
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
            target: 目标实体
        """
        if self.is_expired:
            return
        
        delta = max(0.0, delta)
        self.remaining_time -= delta
        
        self.on_tick(delta, target)
    
    def apply(self, target) -> None:
        """
        应用效果到目标。
        
        调用 on_apply 回调并标记为已应用。
        
        参数：
            target: 目标实体
        """
        if self._is_applied:
            return
        
        self.on_apply(target)
        self._is_applied = True
    
    def remove(self, target) -> None:
        """
        从目标移除效果。
        
        调用 on_remove 回调。
        
        参数：
            target: 目标实体
        """
        if not self._is_applied:
            return
        
        self.on_remove(target)
        self._is_applied = False
    
    @abstractmethod
    def on_apply(self, target) -> None:
        """
        效果首次应用时的回调。
        
        子类应该实现此方法处理应用时的逻辑。
        
        参数：
            target: 目标实体
        """
        pass
    
    @abstractmethod
    def on_remove(self, target) -> None:
        """
        效果移除时的回调。
        
        子类应该实现此方法处理移除时的逻辑（如清理、恢复等）。
        
        参数：
            target: 目标实体
        """
        pass
    
    @abstractmethod
    def on_tick(self, delta: float, target) -> None:
        """
        每帧更新的回调。
        
        子类应该实现此方法处理每帧的逻辑（如造成伤害、刷新状态等）。
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
            target: 目标实体
        """
        pass
    
    def refresh_duration(self) -> None:
        """
        刷新持续时间，将剩余时间重置为总持续时间。
        
        用于效果叠加或刷新的场景。
        """
        self.remaining_time = self.duration
    
    def extend_duration(self, additional_time: float) -> None:
        """
        延长持续时间。
        
        参数：
            additional_time: 要增加的时间（秒）
        """
        additional_time = max(0.0, additional_time)
        self.remaining_time += additional_time
        self.duration += additional_time
