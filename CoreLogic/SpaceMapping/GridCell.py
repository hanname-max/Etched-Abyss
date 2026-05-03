"""
网格单元数据类

GridCell 是二维网格中的基本单元，包含坐标信息、可通行性标识和可见性标识。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GridCell:
    """
    网格单元数据类。
    
    表示二维网格中的一个单元，包含坐标信息、可通行性标识和可见性标识。
    这是一个纯数据结构，不包含任何业务逻辑。
    
    由于使用了 frozen=True，所有属性都是不可变的。
    修改属性需要创建新的 GridCell 实例。
    
    属性：
        x: 单元在网格中的 X 坐标（整型）
        y: 单元在网格中的 Y 坐标（整型）
        is_walkable: 标识该单元是否可通行（默认 True）
        is_visible: 标识该单元是否可见（默认 False，代表被黑雾笼罩）
        
    示例：
        # 创建一个可通行的网格单元，默认被黑雾笼罩
        cell = GridCell(x=0, y=0, is_walkable=True)
        
        # 创建一个不可通行的网格单元（如障碍物），已被探索（可见）
        explored_cell = GridCell(x=1, y=1, is_walkable=False, is_visible=True)
    """
    x: int
    y: int
    is_walkable: bool = True
    is_visible: bool = False

    def __repr__(self) -> str:
        """返回网格单元的字符串表示。"""
        return f"GridCell(x={self.x}, y={self.y}, is_walkable={self.is_walkable}, is_visible={self.is_visible})"

    def __eq__(self, other: object) -> bool:
        """比较两个网格单元是否相等。"""
        if not isinstance(other, GridCell):
            return False
        return (
            self.x == other.x
            and self.y == other.y
            and self.is_walkable == other.is_walkable
            and self.is_visible == other.is_visible
        )

    def __hash__(self) -> int:
        """返回网格单元的哈希值。"""
        return hash((self.x, self.y, self.is_walkable, self.is_visible))
