import pytest
from typing import List, Optional
from CoreLogic import (
    ServiceLocator,
    register_service,
    get_service,
    IGameLogger,
    ITickable,
    GameLogger,
    LogLevel,
    GameLoopManager,
)


class CapturingLogger(GameLogger):
    """
    测试用的日志捕获器，将日志消息捕获到列表中。
    """
    
    def __init__(self, min_level: int = LogLevel.DEBUG):
        super().__init__(min_level)
        self.captured_messages: List[str] = []
        self._output_writers = [self._capture_writer]
    
    def _capture_writer(self, message: str) -> None:
        self.captured_messages.append(message)


class TestTickable(ITickable):
    """
    测试用的 Tickable 实现，记录每次 Tick 的 delta 时间。
    """
    
    def __init__(self, logger: Optional[IGameLogger] = None):
        self.tick_deltas: List[float] = []
        self._logger = logger
    
    def tick(self, delta: float) -> None:
        self.tick_deltas.append(delta)
        if self._logger:
            self._logger.info("Tick executed", delta=delta)


class TestGameLogger:
    """
    GameLogger 单元测试。
    """
    
    def setup_method(self):
        ServiceLocator.reset()
    
    def test_logger_info_message(self):
        logger = CapturingLogger()
        logger.info("Test info message", value=42)
        
        assert len(logger.captured_messages) == 1
        assert "INFO" in logger.captured_messages[0]
        assert "Test info message" in logger.captured_messages[0]
        assert "value=42" in logger.captured_messages[0]
    
    def test_logger_warn_message(self):
        logger = CapturingLogger()
        logger.warn("Test warning", level="high")
        
        assert len(logger.captured_messages) == 1
        assert "WARN" in logger.captured_messages[0]
    
    def test_logger_error_message(self):
        logger = CapturingLogger()
        test_exception = ValueError("Test error")
        logger.error("Test error message", exception=test_exception, code=500)
        
        assert len(logger.captured_messages) == 1
        assert "ERROR" in logger.captured_messages[0]
        assert "ValueError" in logger.captured_messages[0]
    
    def test_logger_combat_message(self):
        logger = CapturingLogger()
        logger.combat("Player attacked", damage=100, critical=True)
        
        assert len(logger.captured_messages) == 1
        assert "COMBAT" in logger.captured_messages[0]
    
    def test_logger_system_message(self):
        logger = CapturingLogger()
        logger.system("Game started", version="1.0.0")
        
        assert len(logger.captured_messages) == 1
        assert "SYSTEM" in logger.captured_messages[0]
    
    def test_logger_level_filtering(self):
        logger = CapturingLogger(min_level=LogLevel.WARN)
        
        logger.info("This should be filtered")
        logger.warn("This should appear")
        logger.error("This should also appear")
        
        assert len(logger.captured_messages) == 2
    
    def test_logger_registered_to_ioc(self):
        logger = GameLogger()
        register_service(IGameLogger, logger)
        
        retrieved = get_service(IGameLogger)
        assert retrieved is logger


class TestGameLoopManager:
    """
    GameLoopManager 单元测试。
    """
    
    def setup_method(self):
        ServiceLocator.reset()
    
    def test_register_tickable(self):
        loop_manager = GameLoopManager()
        tickable = TestTickable()
        
        result = loop_manager.register_tickable(tickable)
        
        assert result is True
        assert loop_manager.is_registered(tickable) is True
        assert loop_manager.get_tickable_count() == 1
    
    def test_register_duplicate_tickable(self):
        loop_manager = GameLoopManager()
        tickable = TestTickable()
        
        loop_manager.register_tickable(tickable)
        result = loop_manager.register_tickable(tickable)
        
        assert result is False
        assert loop_manager.get_tickable_count() == 1
    
    def test_unregister_tickable(self):
        loop_manager = GameLoopManager()
        tickable = TestTickable()
        
        loop_manager.register_tickable(tickable)
        result = loop_manager.unregister_tickable(tickable)
        
        assert result is True
        assert loop_manager.is_registered(tickable) is False
        assert loop_manager.get_tickable_count() == 0
    
    def test_tick_calls_all_tickables(self):
        loop_manager = GameLoopManager()
        tickable1 = TestTickable()
        tickable2 = TestTickable()
        
        loop_manager.register_tickable(tickable1)
        loop_manager.register_tickable(tickable2)
        
        loop_manager.tick(0.016)
        loop_manager.tick(0.017)
        
        assert tickable1.tick_deltas == [0.016, 0.017]
        assert tickable2.tick_deltas == [0.016, 0.017]
    
    def test_tick_statistics(self):
        loop_manager = GameLoopManager()
        
        loop_manager.tick(0.016)
        loop_manager.tick(0.017)
        loop_manager.tick(0.015)
        
        assert loop_manager.get_tick_count() == 3
        assert loop_manager.get_total_elapsed_time() == pytest.approx(0.048)
    
    def test_clear_all_tickables(self):
        loop_manager = GameLoopManager()
        tickable1 = TestTickable()
        tickable2 = TestTickable()
        
        loop_manager.register_tickable(tickable1)
        loop_manager.register_tickable(tickable2)
        assert loop_manager.get_tickable_count() == 2
        
        loop_manager.clear_all_tickables()
        assert loop_manager.get_tickable_count() == 0


class TestIntegration:
    """
    集成测试：GameLogger 注册到 IoC，配合 GameLoopManager 使用。
    """
    
    def setup_method(self):
        ServiceLocator.reset()
    
    def test_logger_in_ioc_with_tickable(self):
        logger = CapturingLogger(min_level=LogLevel.DEBUG)
        register_service(IGameLogger, logger)
        
        loop_manager = GameLoopManager()
        tickable = TestTickable(logger=get_service(IGameLogger))
        loop_manager.register_tickable(tickable)
        
        loop_manager.tick(0.016)
        loop_manager.tick(0.017)
        
        assert len(tickable.tick_deltas) == 2
        assert tickable.tick_deltas[0] == 0.016
        assert tickable.tick_deltas[1] == 0.017
        
        assert len(logger.captured_messages) == 2
        assert "delta=0.016" in logger.captured_messages[0]
        assert "delta=0.017" in logger.captured_messages[1]
    
    def test_multiple_tickables_execution_order(self):
        loop_manager = GameLoopManager()
        execution_order = []
        
        class OrderedTickable(ITickable):
            def __init__(self, name: str):
                self.name = name
            
            def tick(self, delta: float) -> None:
                execution_order.append(self.name)
        
        tickable1 = OrderedTickable("A")
        tickable2 = OrderedTickable("B")
        tickable3 = OrderedTickable("C")
        
        loop_manager.register_tickable(tickable1)
        loop_manager.register_tickable(tickable2)
        loop_manager.register_tickable(tickable3)
        
        loop_manager.tick(0.016)
        
        assert execution_order == ["A", "B", "C"]
    
    def test_register_during_tick(self):
        loop_manager = GameLoopManager()
        tickable2_registered = []
        
        class LateRegisteringTickable(ITickable):
            def tick(self, delta: float) -> None:
                loop_manager.register_tickable(Tickable2())
        
        class Tickable2(ITickable):
            def tick(self, delta: float) -> None:
                tickable2_registered.append(True)
        
        loop_manager.register_tickable(LateRegisteringTickable())
        
        loop_manager.tick(0.016)
        assert len(tickable2_registered) == 0
        
        loop_manager.tick(0.016)
        assert len(tickable2_registered) == 1


class TestUsageDemo:
    """
    演示如何使用 GameLogger 和 GameLoopManager。
    """
    
    def test_demo_game_logger_usage(self):
        logger = CapturingLogger(min_level=LogLevel.DEBUG)
        
        logger.system("游戏启动", version="1.0.0")
        logger.info("初始化数据加载器")
        logger.combat("敌人生成", enemy_id="e001", hp=100)
        logger.warn("资源加载缓慢", timeout=5.0)
        
        try:
            raise ValueError("测试异常")
        except Exception as e:
            logger.error("发生错误", exception=e)
        
        assert len(logger.captured_messages) == 5
    
    def test_demo_game_loop_usage(self):
        loop_manager = GameLoopManager()
        tick_deltas = []
        
        class SimpleMovementSystem(ITickable):
            def __init__(self):
                self.position = 0.0
                self.velocity = 100.0
            
            def tick(self, delta: float) -> None:
                self.position += self.velocity * delta
                tick_deltas.append(delta)
        
        move_system = SimpleMovementSystem()
        loop_manager.register_tickable(move_system)
        
        loop_manager.tick(0.016)
        loop_manager.tick(0.016)
        loop_manager.tick(0.016)
        
        assert len(tick_deltas) == 3
        assert move_system.position == pytest.approx(4.8)
