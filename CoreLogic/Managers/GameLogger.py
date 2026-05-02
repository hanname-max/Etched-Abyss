"""
游戏日志实现

GameLogger 是 IGameLogger 接口的默认实现。
提供不同级别的日志打印能力，支持控制台输出和扩展。

============================================================================
【架构规范强制声明】
============================================================================

GameLogger 应该通过 ServiceLocator 获取，而不是直接实例化。

正确示例：
    from CoreLogic import get_service, IGameLogger, GameLogger, register_service
    
    # 注册到 IoC 容器
    register_service(IGameLogger, GameLogger())
    
    # 获取并使用
    logger = get_service(IGameLogger)
    logger.info("初始化完成")

错误示例（严禁使用）：
    # 直接实例化
    logger = GameLogger()
============================================================================
"""

import sys
import traceback
from datetime import datetime
from typing import Any, Optional, List, Callable

from CoreLogic.Interfaces.IGameLogger import IGameLogger


class LogLevel:
    """
    日志级别枚举。
    
    用于控制日志输出的详细程度。
    """
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    COMBAT = 4
    SYSTEM = 5


class GameLogger(IGameLogger):
    """
    游戏日志默认实现。
    
    实现了 IGameLogger 接口，提供不同级别的日志打印能力。
    支持自定义输出目标、过滤级别和格式化。
    
    使用示例：
        logger = GameLogger()
        logger.info("玩家已登录", player_id="p001")
        logger.warn("内存使用过高", usage="85%")
        logger.error("网络连接失败", exception=ConnectionError("timeout"))
        logger.combat("攻击命中", damage=100, critical=True)
        logger.system("游戏启动", version="1.0.0")
    """

    def __init__(self, min_level: int = LogLevel.INFO):
        """
        初始化日志器。
        
        参数：
            min_level: 最小日志级别，低于此级别的日志将不会被输出
        """
        self._min_level = min_level
        self._output_writers: List[Callable[[str], None]] = [self._default_writer]
        self._formatter: Callable[..., str] = self._default_formatter
        self._enabled: bool = True

    def _default_writer(self, message: str) -> None:
        """
        默认的日志写入器，输出到标准输出。
        """
        sys.stdout.write(message + '\n')
        sys.stdout.flush()

    @staticmethod
    def _default_formatter(level_name: str, message: str, **kwargs: Any) -> str:
        """
        默认的日志格式化器。
        
        格式：[时间戳] [级别] 消息 [附加信息]
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        parts = [f"[{timestamp}]", f"[{level_name:>6}]", message]
        
        if kwargs:
            extra_parts = []
            for key, value in kwargs.items():
                if key == 'exception':
                    continue
                extra_parts.append(f"{key}={value}")
            if extra_parts:
                parts.append("[" + ", ".join(extra_parts) + "]")
        
        return " ".join(parts)

    def _log(self, log_level: int, level_name: str, message: str, **kwargs: Any) -> None:
        """
        内部日志方法，执行级别检查和格式化输出。
        """
        if not self._enabled or log_level < self._min_level:
            return
        
        formatted = self._formatter(level_name, message, **kwargs)
        
        exception = kwargs.get('exception')
        if exception is not None:
            tb_str = ''.join(traceback.format_exception(
                type(exception), exception, exception.__traceback__
            ))
            formatted = f"{formatted}\n{tb_str}"
        
        for writer in self._output_writers:
            writer(formatted)

    def info(self, message: str, **kwargs: Any) -> None:
        """
        记录信息级别的日志。
        
        用于记录一般信息，如系统状态、初始化进度等。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数，会附加到日志中
        """
        self._log(LogLevel.INFO, "INFO", message, **kwargs)

    def warn(self, message: str, **kwargs: Any) -> None:
        """
        记录警告级别的日志。
        
        用于记录可能影响系统但不影响继续运行的情况。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数，会附加到日志中
        """
        self._log(LogLevel.WARN, "WARN", message, **kwargs)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs: Any) -> None:
        """
        记录错误级别的日志。
        
        用于记录错误和异常情况。
        
        参数：
            message: 日志消息
            exception: 可选的异常对象
            **kwargs: 额外的关键字参数，会附加到日志中
        """
        self._log(LogLevel.ERROR, "ERROR", message, exception=exception, **kwargs)

    def combat(self, message: str, **kwargs: Any) -> None:
        """
        记录战斗相关的日志。
        
        用于记录战斗系统中的关键事件，如攻击、死亡、技能释放等。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数，会附加到日志中
        """
        self._log(LogLevel.COMBAT, "COMBAT", message, **kwargs)

    def system(self, message: str, **kwargs: Any) -> None:
        """
        记录系统级别的日志。
        
        用于记录游戏系统的关键事件，如游戏启动、存档加载、关卡切换等。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数，会附加到日志中
        """
        self._log(LogLevel.SYSTEM, "SYSTEM", message, **kwargs)

    def set_min_level(self, level: int) -> None:
        """
        设置最小日志级别。
        
        参数：
            level: 最小日志级别，低于此级别的日志将不会被输出
        """
        self._min_level = level

    def add_writer(self, writer: Callable[[str], None]) -> None:
        """
        添加自定义的日志写入器。
        
        可以用于将日志输出到文件、网络或其他目标。
        
        参数：
            writer: 一个接受字符串参数的可调用对象
        """
        if writer not in self._output_writers:
            self._output_writers.append(writer)

    def remove_writer(self, writer: Callable[[str], None]) -> None:
        """
        移除自定义的日志写入器。
        
        参数：
            writer: 要移除的写入器
        """
        if writer in self._output_writers and writer is not self._default_writer:
            self._output_writers.remove(writer)

    def set_formatter(self, formatter: Callable[[str, str, Any], str]) -> None:
        """
        设置自定义的日志格式化器。
        
        参数：
            formatter: 一个接受 (级别名, 消息, **kwargs) 并返回格式化字符串的可调用对象
        """
        self._formatter = formatter

    def enable(self) -> None:
        """
        启用日志输出。
        """
        self._enabled = True

    def disable(self) -> None:
        """
        禁用日志输出。
        """
        self._enabled = False
