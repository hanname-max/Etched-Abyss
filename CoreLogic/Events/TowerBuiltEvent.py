"""
塔建造事件

TowerBuiltEvent 用于在防御塔建造完成时通知其他系统。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯粹的数据容器事件，用于跨域通信。
当 BuildManager 成功建造防御塔时，会发布此事件，
其他系统（如 DynamicRepathingSystem）可以订阅并处理。

使用场景：
- 动态重寻路系统：检查敌人路径是否被阻断，触发重新寻路
- UI系统：显示建造成功特效或提示
- 经济系统：扣除资源
- 成就系统：检查建造相关成就
============================================================================
"""

from dataclasses import dataclass


@dataclass
class TowerBuiltEvent:
    """
    塔建造事件。
    
    当 BuildManager 成功建造防御塔时发布此事件。
    
    属性：
        tower_entity_id: 建造完成的防御塔实体 ID
        grid_x: 塔所在网格的 X 坐标
        grid_y: 塔所在网格的 Y 坐标
        tower_config_id: 防御塔配置的 ID
    
    使用示例：
        # 订阅塔建造事件
        from CoreLogic import subscribe, TowerBuiltEvent
        
        def on_tower_built(event: TowerBuiltEvent) -> None:
            print(f"塔 {event.tower_config_id} 已建造在 ({event.grid_x}, {event.grid_y})")
        
        subscribe(TowerBuiltEvent, on_tower_built)
        
        # 发布塔建造事件（通常由 BuildManager 自动发布）
        from CoreLogic import publish
        publish(TowerBuiltEvent(tower_entity_id=1, grid_x=5, grid_y=3, tower_config_id="tower_arrow_001"))
    """
    
    tower_entity_id: int
    grid_x: int
    grid_y: int
    tower_config_id: str
