"""
游戏日志接口定义

IGameLogger 是所有日志实现的基接口。
用于不同级别的信息透出，便于调试和监控。

============================================================================
【架构规范强制声明】
============================================================================

所有日志记录都应该通过此接口进行。
业务逻辑不应该直接依赖具体的日志实现，而应该依赖此接口。

正确示例：
    # 依赖抽象接口
    def __init__(self, logger: IGameLogger):
        self._logger = logger
    
    # 使用接口方法
    self._logger.info("玩家已登录")

错误示例（严禁使用）：
    # 直接使用 print
    print("玩家已登录")
    
    # 或直接依赖具体实现
    from CoreLogic.Managers.GameLogger import GameLogger
    logger = GameLogger()
============================================================================
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class IGameLogger(ABC):
    """
    游戏日志基接口。
    
    定义了不同级别日志记录的统一接口。
    所有具体的日志实现都应该实现此接口。
    
    使用示例：
        # 通过 ServiceLocator 获取日志器
        logger = get_service(IGameLogger)
        
        # 记录不同级别的日志
        logger.info("初始化完成")
        logger.warn("资源不足")
        logger.error("发生错误", exception=e)
        logger.combat("敌人死亡", {"enemy_id": "e001", "reward": 100})
        logger.system("游戏启动")
    """

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """
        记录信息级别的日志。
        
        用于记录一般信息，如系统状态、初始化进度等。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数，会附加到日志中
        """
        pass

    @abstractmethod
    def warn(self, message: str, **kwargs: Any) -> None:
        """
        记录警告级别的日志。
        
        用于记录可能影响系统但不影响继续运行的情况。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数，会附加到日志中
        """
        pass

    @abstractmethod
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs: Any) -> None:
        """
        记录错误级别的日志。
        
        用于记录错误和异常情况。
        
        参数：
            message: 日志消息
            exception: 可选的异常对象
            **kwargs: 额外的关键字参数，会附加到日志中
        """
        pass

    @abstractmethod
    def combat(self, message: str, **kwargs: Any) -> None:
        """
        记录战斗相关的日志。
        
        用于记录战斗系统中的关键事件，如攻击、死亡、技能释放等。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数，会附加到日志中
        """
        pass

    @abstractmethod
    def system(self, message: str, **kwargs: Any) -> None:
        """
        记录系统级别的日志。
        
        用于记录游戏系统的关键事件，如游戏启动、存档加载、关卡切换等。
        
        参数：
            message: 日志消息
            **kwargs: 额外的关键字参数，会附加到日志中
        """
        pass
