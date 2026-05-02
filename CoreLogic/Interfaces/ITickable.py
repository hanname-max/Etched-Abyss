"""
可更新接口定义

ITickable 是所有需要每帧更新的系统的基接口。
用于将需要时间推演的系统注册到 GameLoopManager。

============================================================================
【架构规范强制声明】
============================================================================

所有需要每帧更新的系统都应该实现此接口。
GameLoopManager 会在每一帧调用所有已注册 ITickable 的 Tick 方法。

正确示例：
    class MoveSystem(ITickable):
        def tick(self, delta: float):
            # 更新所有实体的位置
            for entity in self._entities:
                entity.position += entity.velocity * delta
    
    # 注册到 GameLoopManager
    loop_manager.register_tickable(move_system)

错误示例（严禁使用）：
    # 在多个地方分散更新逻辑
    def update_all_systems(delta):
        move_system.update(delta)
        cooldown_system.update(delta)
        animation_system.update(delta)
============================================================================
"""

from abc import ABC, abstractmethod


class ITickable(ABC):
    """
    可更新基接口。
    
    定义了每帧更新的统一接口。
    所有需要每帧更新的系统（如移动系统、冷却系统、动画系统等）都应该实现此接口。
    
    使用示例：
        class CooldownSystem(ITickable):
            def __init__(self):
                self._cooldowns = {}
            
            def tick(self, delta: float):
                # 更新所有冷却
                for skill_id, remaining in list(self._cooldowns.items()):
                    remaining -= delta
                    if remaining <= 0:
                        del self._cooldowns[skill_id]
                    else:
                        self._cooldowns[skill_id] = remaining
        
        # 注册到 GameLoopManager
        loop_manager = get_service(GameLoopManager)
        loop_manager.register_tickable(cooldown_system)
    """

    @abstractmethod
    def tick(self, delta: float) -> None:
        """
        每帧更新方法。
        
        GameLoopManager 会在每一帧调用此方法。
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
        """
        pass
