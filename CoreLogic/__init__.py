"""
蚀刻深渊核心逻辑库

纯逻辑层核心库，用于塔防游戏《蚀刻深渊》。

============================================================================
【架构规范强制声明】
============================================================================

不同域（如战斗系统、经济系统、UI系统、存档系统等）之间的交互，
必须通过投递 Event 进行，严禁跨域的强耦合直接调用。

正确示例：
    # 战斗系统发布事件
    publish(EnemyKilledEvent(enemy_id="enemy_001", reward=100))
    
    # 经济系统订阅并处理
    subscribe(EnemyKilledEvent, self._on_enemy_killed)
    
错误示例（严禁使用）：
    # 战斗系统直接调用经济系统方法（强耦合）
    self.economic_system.add_gold(100)

违反此规范的代码将被视为架构缺陷，需要重构。
============================================================================
"""

from CoreLogic.Core import (
    ServiceLocator,
    register_service,
    get_service,
    try_get_service,
    is_service_registered,
    EventBus,
    subscribe,
    unsubscribe,
    publish,
)
from CoreLogic.Interfaces import (
    IEvent,
    IDataLoader,
    IGameLogger,
    ITickable,
    IComponent,
    IEntity,
    IUpdateable,
)
from CoreLogic.DTOs import (
    BaseConfigDTO,
    EnemyConfigDTO,
    TowerConfigDTO,
    WaveConfigDTO,
    EnemySpawnConfig,
)
from CoreLogic.DataLoaders import (
    MockDataLoader,
)
from CoreLogic.Managers import (
    GameLogger,
    LogLevel,
    GameLoopManager,
    EntityManager,
    WaveManager,
    SpawnTask,
)
from CoreLogic.SpaceMapping import (
    GridCell,
    GridMap,
    Pathfinder,
    PathNode,
)
from CoreLogic.Components import (
    TransformComponent,
    HealthComponent,
    MovementComponent,
)
from CoreLogic.Events import (
    EntityDeathEvent,
)
from CoreLogic.Systems import (
    HealthSystem,
    DeathSystem,
)
from CoreLogic.Systems.HealthSystem import (
    DeathContext,
    OnDeathCallback,
)

__all__ = [
    'ServiceLocator',
    'register_service',
    'get_service',
    'try_get_service',
    'is_service_registered',
    'EventBus',
    'subscribe',
    'unsubscribe',
    'publish',
    'IEvent',
    'IDataLoader',
    'IGameLogger',
    'ITickable',
    'IComponent',
    'IEntity',
    'IUpdateable',
    'BaseConfigDTO',
    'EnemyConfigDTO',
    'TowerConfigDTO',
    'WaveConfigDTO',
    'EnemySpawnConfig',
    'MockDataLoader',
    'GameLogger',
    'LogLevel',
    'GameLoopManager',
    'EntityManager',
    'WaveManager',
    'SpawnTask',
    'GridCell',
    'GridMap',
    'Pathfinder',
    'PathNode',
    'TransformComponent',
    'HealthComponent',
    'MovementComponent',
    'EntityDeathEvent',
    'HealthSystem',
    'DeathSystem',
    'DeathContext',
    'OnDeathCallback',
]
