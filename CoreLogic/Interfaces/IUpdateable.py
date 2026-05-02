"""
可更新组件接口定义

IUpdateable 是需要每帧更新的 Component 的接口。
用于标记那些需要在 EntityManager 的 Update 阶段被调用的 Component。

============================================================================
【架构规范强制声明】
============================================================================

与 ITickable（用于 System 级别）不同，IUpdateable 是 Component 级别的更新接口。
Component 实现此接口后，EntityManager 会在每一帧的 Update 阶段自动调用其 Update 方法。

正确示例：
    @dataclass
    class CooldownComponent(IUpdateable):
        remaining: float = 0.0
        
        def update(self, delta: float):
            if self.remaining > 0:
                self.remaining -= delta

错误示例（严禁使用）：
    # 在 Component 中包含复杂的业务逻辑
    class CooldownComponent:
        def update(self, delta):
            # 不应该在这里直接修改其他组件或实体
            entity = get_current_entity()
            entity.get_component(HealthComponent).current -= 1
============================================================================
"""

from abc import ABC, abstractmethod


class IUpdateable(ABC):
    """
    可更新组件接口。
    
    Component 实现此接口后，EntityManager 会在每一帧的 Update 阶段
    自动调用其 Update 方法。
    
    与 ITickable 的区别：
    - ITickable: 用于 System 级别的更新，由 GameLoopManager 管理
    - IUpdateable: 用于 Component 级别的更新，由 EntityManager 管理
    
    使用示例：
        @dataclass
        class LifetimeComponent(IUpdateable):
            time: float = 0.0
            max_time: float = 5.0
            
            def update(self, delta: float):
                self.time += delta
                if self.time >= self.max_time:
                    # 标记实体需要销毁
                    pass
        
        # EntityManager 会自动遍历所有实体的 IUpdateable 组件并调用 update
        entity_manager.update(delta)
    """

    @abstractmethod
    def update(self, delta: float) -> None:
        """
        每帧更新方法。
        
        EntityManager 会在每一帧的 Update 阶段调用此方法。
        
        参数：
            delta: 自上一帧以来经过的时间（秒）
        """
        pass
