"""
配置数据传输对象基类

BaseConfigDTO 是所有外部配置数据 DTO 的基类。
所有从 JSON 加载的配置数据都应该继承此类。

============================================================================
【架构规范强制声明】
============================================================================

所有配置 DTO 都应该：
1. 从 BaseConfigDTO 继承
2. 使用 @dataclass(frozen=True) 装饰器确保不可变性
3. 只包含数据字段，不包含业务逻辑
4. 提供 from_dict 类方法用于从字典创建实例

============================================================================
"""

from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, Type, TypeVar

T = TypeVar('T', bound='BaseConfigDTO')


@dataclass(frozen=True)
class BaseConfigDTO(ABC):
    """
    配置数据传输对象基类。
    
    所有外部配置数据（如防御塔、敌人、关卡波次等）都应该继承此类。
    这是一个抽象基类，定义了配置 DTO 的通用接口。
    
    属性：
        id: 配置项的唯一标识符
        name: 配置项的可读名称
        
    示例：
        @dataclass(frozen=True)
        class EnemyConfigDTO(BaseConfigDTO):
            hp: int
            speed: float
            damage: int
            
        # 从字典创建
        enemy = EnemyConfigDTO.from_dict({
            "id": "enemy_001",
            "name": "基础影裔",
            "hp": 100,
            "speed": 1.5,
            "damage": 10
        })
    """
    id: str
    name: str

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        从字典创建 DTO 实例。
        
        子类可以重写此方法以提供自定义的反序列化逻辑。
        
        参数：
            data: 包含配置数据的字典
            
        返回：
            DTO 实例
            
        异常：
            TypeError: 如果缺少必填字段
            ValueError: 如果字段值无效
        """
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """
        将 DTO 转换为字典。
        
        用于序列化或调试目的。
        
        返回：
            包含所有字段的字典
        """
        return {
            f.name: getattr(self, f.name)
            for f in self.__class__.__dataclass_fields__.values()
        }

    def __repr__(self) -> str:
        """返回 DTO 的字符串表示。"""
        fields = ", ".join(
            f"{f.name}={getattr(self, f.name)!r}"
            for f in self.__class__.__dataclass_fields__.values()
        )
        return f"{self.__class__.__name__}({fields})"
