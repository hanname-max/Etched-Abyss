"""
游戏循环管理器实现

GameLoopManager 是整个游戏逻辑的时间推演入口。
负责管理所有需要每帧更新的系统，并统一调用它们的 Tick 方法。

============================================================================
【架构规范强制声明】
============================================================================

GameLoopManager 应该通过 ServiceLocator 获取，而不是直接实例化。
Tick 方法是整个游戏逻辑的唯一时间推演入口，严禁在其他地方分散更新逻辑。

正确示例：
    from CoreLogic import get_service, GameLoopManager, register_service
    
    # 注册到 IoC 容器
    register_service(GameLoopManager, GameLoopManager())
    
    # 获取并使用
    loop_manager = get_service(GameLoopManager)
    loop_manager.register_tickable(move_system)
    loop_manager.register_tickable(cooldown_system)
    
    # 游戏主循环
    while running:
        delta = get_frame_delta()
        loop_manager.tick(delta)

错误示例（严禁使用）：
    # 分散的更新逻辑
    def update_game(delta):
        move_system.tick(delta)
        cooldown_system.tick(delta)
        animation_system.tick(delta)
============================================================================
"""

from typing import List, Optional, Set

from CoreLogic.Interfaces.ITickable import ITickable


class GameLoopManager:
    """
    游戏循环管理器。
    
    负责管理所有需要每帧更新的系统（ITickable 实现），
    并在每一帧统一调用它们的 Tick 方法。
    
    这是整个游戏逻辑的唯一时间推演入口。
    
    使用示例：
        loop_manager = GameLoopManager()
        
        # 注册需要更新的系统
        loop_manager.register_tickable(move_system)
        loop_manager.register_tickable(cooldown_system)
        
        # 在游戏主循环中调用
        while game_running:
            delta = calculate_delta_time()
            loop_manager.tick(delta)
    """

    def __init__(self):
        """
        初始化游戏循环管理器。
        """
        self._tickables: List[ITickable] = []
        self._pending_registrations: List[ITickable] = []
        self._pending_unregistrations: Set[ITickable] = set()
        self._is_ticking: bool = False
        self._total_elapsed_time: float = 0.0
        self._tick_count: int = 0

    def register_tickable(self, tickable: ITickable) -> bool:
        """
        注册一个需要每帧更新的系统。
        
        如果在 Tick 执行过程中调用，注册将延迟到当前 Tick 完成后生效。
        
        参数：
            tickable: 实现了 ITickable 接口的系统实例
            
        返回：
            True 如果注册成功，False 如果已经注册过
        """
        if tickable in self._tickables or tickable in self._pending_registrations:
            return False
        
        if self._is_ticking:
            self._pending_registrations.append(tickable)
        else:
            self._tickables.append(tickable)
        
        return True

    def unregister_tickable(self, tickable: ITickable) -> bool:
        """
        注销一个不再需要每帧更新的系统。
        
        如果在 Tick 执行过程中调用，注销将延迟到当前 Tick 完成后生效。
        
        参数：
            tickable: 要注销的系统实例
            
        返回：
            True 如果注销成功，False 如果未找到
        """
        if self._is_ticking:
            if tickable in self._tickables and tickable not in self._pending_unregistrations:
                self._pending_unregistrations.add(tickable)
                return True
            if tickable in self._pending_registrations:
                self._pending_registrations.remove(tickable)
                return True
            return False
        else:
            if tickable in self._tickables:
                self._tickables.remove(tickable)
                return True
            return False

    def is_registered(self, tickable: ITickable) -> bool:
        """
        检查一个系统是否已注册（包括待注册的）。
        
        参数：
            tickable: 要检查的系统实例
            
        返回：
            True 如果已注册或待注册
        """
        return (
            tickable in self._tickables 
            or tickable in self._pending_registrations
        ) and tickable not in self._pending_unregistrations

    def tick(self, delta: float) -> None:
        """
        执行一帧的时间推演。
        
        这是整个游戏逻辑的唯一时间推演入口。
        会按注册顺序调用所有已注册 ITickable 的 Tick 方法。
        
        参数：
            delta: 自上一帧以来经过的时间（秒），应为非负值
        """
        if delta < 0:
            delta = 0.0
        
        self._is_ticking = True
        self._total_elapsed_time += delta
        self._tick_count += 1
        
        for tickable in self._tickables:
            if tickable in self._pending_unregistrations:
                continue
            tickable.tick(delta)
        
        self._is_ticking = False
        self._process_pending_operations()

    def _process_pending_operations(self) -> None:
        """
        处理待处理的注册和注销操作。
        """
        for tickable in self._pending_registrations:
            if tickable not in self._tickables:
                self._tickables.append(tickable)
        self._pending_registrations.clear()
        
        for tickable in self._pending_unregistrations:
            if tickable in self._tickables:
                self._tickables.remove(tickable)
        self._pending_unregistrations.clear()

    def clear_all_tickables(self) -> None:
        """
        清除所有已注册的系统。
        
        如果在 Tick 执行过程中调用，清除将延迟到当前 Tick 完成后生效。
        """
        if self._is_ticking:
            self._pending_unregistrations.update(self._tickables)
            self._pending_registrations.clear()
        else:
            self._tickables.clear()
            self._pending_registrations.clear()
            self._pending_unregistrations.clear()

    def get_tickable_count(self) -> int:
        """
        获取当前已注册的系统数量（不包括待注册和待注销的）。
        
        返回：
            已注册系统的数量
        """
        return len(self._tickables)

    def get_total_elapsed_time(self) -> float:
        """
        获取累计经过的总时间。
        
        返回：
            自管理器创建以来累计的时间（秒）
        """
        return self._total_elapsed_time

    def get_tick_count(self) -> int:
        """
        获取 Tick 调用的总次数。
        
        返回：
            Tick 方法被调用的次数
        """
        return self._tick_count

    def reset_statistics(self) -> None:
        """
        重置统计信息（累计时间和 Tick 计数）。
        """
        self._total_elapsed_time = 0.0
        self._tick_count = 0
