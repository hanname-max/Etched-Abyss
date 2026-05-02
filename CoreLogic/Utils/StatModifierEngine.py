"""
属性修饰器引擎

Stat Modifier Engine 实现动态数值结算引擎，用于灵活地管理游戏中的各种属性（攻击力、攻速等）。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯数据计算引擎，不涉及任何事件或服务定位器。
所有的数值计算都应该通过此引擎进行，以保证属性系统的一致性。
============================================================================
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class ModifierType(Enum):
    """
    属性修饰器类型枚举。
    
    定义修饰器如何影响基础属性值的计算方式。
    
    成员：
        Additive: 加法修饰器，直接加到基础值上
        Multiplicative: 乘法修饰器，以系数形式乘到总和上
        
    计算规则：
        最终值 = (基础值 + 所有加法修饰器总和) * (1 + 所有乘法修饰器总和)
        
    示例：
        基础值: 100
        加法修饰器: +20, +30
        乘法修饰器: +10% (+0.1), +20% (+0.2)
        
        最终值 = (100 + 20 + 30) * (1 + 0.1 + 0.2) = 150 * 1.3 = 195
    """
    
    Additive = 1
    Multiplicative = 2


class StatModifier:
    """
    属性修饰器。
    
    表示对某个属性的一个修饰，可以是加法或乘法类型。
    
    属性：
        modifier_type: 修饰器类型（加法/乘法）
        value: 修饰器的数值
        source: 可选的修饰器来源标识（用于追踪来源，如"装备_暴击剑"）
        modifier_id: 唯一标识符，用于精确移除修饰器
        
    使用示例：
        # 创建一个 +20 攻击力的加法修饰器
        damage_buff = StatModifier(
            modifier_type=ModifierType.Additive,
            value=20.0,
            source="力量药水"
        )
        
        # 创建一个 +20% 攻击速度的乘法修饰器
        speed_buff = StatModifier(
            modifier_type=ModifierType.Multiplicative,
            value=0.2,
            source="狂暴技能"
        )
    """
    
    def __init__(
        self,
        modifier_type: ModifierType,
        value: float,
        source: Optional[str] = None,
        modifier_id: Optional[UUID] = None
    ) -> None:
        """
        初始化属性修饰器。
        
        参数：
            modifier_type: 修饰器类型（加法/乘法）
            value: 修饰器的数值
            source: 可选的来源标识
            modifier_id: 可选的唯一标识符，不提供则自动生成
        """
        self._modifier_type: ModifierType = modifier_type
        self._value: float = value
        self._source: Optional[str] = source
        self._modifier_id: UUID = modifier_id if modifier_id is not None else uuid4()
    
    @property
    def modifier_type(self) -> ModifierType:
        """获取修饰器类型。"""
        return self._modifier_type
    
    @property
    def value(self) -> float:
        """获取修饰器数值。"""
        return self._value
    
    @property
    def source(self) -> Optional[str]:
        """获取修饰器来源标识。"""
        return self._source
    
    @property
    def modifier_id(self) -> UUID:
        """获取修饰器唯一标识符。"""
        return self._modifier_id
    
    def __repr__(self) -> str:
        return (
            f"StatModifier(type={self._modifier_type.name}, "
            f"value={self._value}, source={self._source!r})"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典，用于存档或网络传输。
        
        返回：
            包含修饰器所有信息的字典
        """
        return {
            "modifier_type": self._modifier_type.name,
            "value": self._value,
            "source": self._source,
            "modifier_id": str(self._modifier_id)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatModifier':
        """
        从字典反序列化创建修饰器。
        
        参数：
            data: 包含修饰器信息的字典
            
        返回：
            StatModifier 实例
        """
        return cls(
            modifier_type=ModifierType[data["modifier_type"]],
            value=float(data["value"]),
            source=data.get("source"),
            modifier_id=UUID(data["modifier_id"]) if data.get("modifier_id") else None
        )


class ModifiableStat:
    """
    可修改的属性。
    
    包装一个基础属性值，并支持动态添加/移除修饰器，实时计算最终数值。
    
    计算规则：
        最终值 = (基础值 + 所有加法修饰器总和) * (1 + 所有乘法修饰器总和)
    
    属性：
        base_value: 基础属性值（可读写）
        name: 可选的属性名称（用于调试和日志）
        
    使用示例：
        # 创建一个攻击力属性，基础值为 100
        attack_damage = ModifiableStat(base_value=100.0, name="攻击力")
        
        # 添加加法修饰器：+20 伤害
        buff1 = StatModifier(ModifierType.Additive, 20.0, source="力量药水")
        attack_damage.add_modifier(buff1)
        
        # 添加乘法修饰器：+20% 伤害
        buff2 = StatModifier(ModifierType.Multiplicative, 0.2, source="狂暴技能")
        attack_damage.add_modifier(buff2)
        
        # 获取最终值：(100 + 20) * (1 + 0.2) = 144
        final_value = attack_damage.get_value()  # 返回 144.0
        
        # 移除某个修饰器
        attack_damage.remove_modifier(buff1.modifier_id)
    """
    
    def __init__(self, base_value: float = 0.0, name: Optional[str] = None) -> None:
        """
        初始化可修改属性。
        
        参数：
            base_value: 基础属性值，默认为 0.0
            name: 可选的属性名称
        """
        self._base_value: float = base_value
        self._name: Optional[str] = name
        self._modifiers: List[StatModifier] = []
        self._cached_value: Optional[float] = None
        self._is_dirty: bool = True
    
    @property
    def base_value(self) -> float:
        """获取或设置基础属性值。"""
        return self._base_value
    
    @base_value.setter
    def base_value(self, value: float) -> None:
        self._base_value = value
        self._is_dirty = True
    
    @property
    def name(self) -> Optional[str]:
        """获取属性名称。"""
        return self._name
    
    def add_modifier(self, modifier: StatModifier) -> None:
        """
        添加一个属性修饰器。
        
        参数：
            modifier: 要添加的 StatModifier 实例
        """
        self._modifiers.append(modifier)
        self._is_dirty = True
    
    def remove_modifier(self, modifier_id: UUID) -> bool:
        """
        按 ID 移除一个修饰器。
        
        参数：
            modifier_id: 要移除的修饰器的唯一标识符
            
        返回：
            True 如果成功移除，False 如果未找到
        """
        for i, modifier in enumerate(self._modifiers):
            if modifier.modifier_id == modifier_id:
                del self._modifiers[i]
                self._is_dirty = True
                return True
        return False
    
    def remove_all_modifiers(self, source: Optional[str] = None) -> int:
        """
        移除所有修饰器，或按来源移除。
        
        参数：
            source: 可选的来源标识。如果提供，只移除来自该来源的修饰器；
                   如果为 None，移除所有修饰器。
            
        返回：
            被移除的修饰器数量
        """
        if source is None:
            count = len(self._modifiers)
            self._modifiers.clear()
            self._is_dirty = True
            return count
        
        removed_count = 0
        new_modifiers: List[StatModifier] = []
        for modifier in self._modifiers:
            if modifier.source == source:
                removed_count += 1
            else:
                new_modifiers.append(modifier)
        
        if removed_count > 0:
            self._modifiers = new_modifiers
            self._is_dirty = True
        
        return removed_count
    
    def get_modifiers(self, modifier_type: Optional[ModifierType] = None) -> List[StatModifier]:
        """
        获取所有修饰器，或按类型筛选。
        
        参数：
            modifier_type: 可选的类型筛选条件
            
        返回：
            符合条件的修饰器列表（新列表，非引用）
        """
        if modifier_type is None:
            return list(self._modifiers)
        return [m for m in self._modifiers if m.modifier_type == modifier_type]
    
    def get_value(self) -> float:
        """
        计算并返回最终属性值。
        
        计算规则：
            最终值 = (基础值 + 所有加法修饰器总和) * (1 + 所有乘法修饰器总和)
        
        此方法会缓存计算结果，只有当修饰器或基础值变化时才会重新计算。
        
        返回：
            最终计算出的属性值
        """
        if not self._is_dirty and self._cached_value is not None:
            return self._cached_value
        
        additive_sum: float = 0.0
        multiplicative_sum: float = 0.0
        
        for modifier in self._modifiers:
            if modifier.modifier_type == ModifierType.Additive:
                additive_sum += modifier.value
            elif modifier.modifier_type == ModifierType.Multiplicative:
                multiplicative_sum += modifier.value
        
        additive_total = self._base_value + additive_sum
        final_value = additive_total * (1.0 + multiplicative_sum)
        
        self._cached_value = final_value
        self._is_dirty = False
        
        return final_value
    
    def get_breakdown(self) -> Dict[str, Any]:
        """
        获取属性计算的详细分解信息（用于调试和UI显示）。
        
        返回：
            包含计算分解信息的字典，结构如下：
            {
                "base_value": float,
                "additive_modifiers": [
                    {"value": float, "source": str | None}, ...
                ],
                "additive_total": float,
                "multiplicative_modifiers": [
                    {"value": float, "source": str | None}, ...
                ],
                "multiplicative_total": float,
                "final_value": float
            }
        """
        additive_modifiers: List[Dict[str, Any]] = []
        multiplicative_modifiers: List[Dict[str, Any]] = []
        additive_sum: float = 0.0
        multiplicative_sum: float = 0.0
        
        for modifier in self._modifiers:
            info = {
                "value": modifier.value,
                "source": modifier.source
            }
            if modifier.modifier_type == ModifierType.Additive:
                additive_modifiers.append(info)
                additive_sum += modifier.value
            elif modifier.modifier_type == ModifierType.Multiplicative:
                multiplicative_modifiers.append(info)
                multiplicative_sum += modifier.value
        
        additive_total = self._base_value + additive_sum
        final_value = additive_total * (1.0 + multiplicative_sum)
        
        return {
            "base_value": self._base_value,
            "additive_modifiers": additive_modifiers,
            "additive_total": additive_total,
            "multiplicative_modifiers": multiplicative_modifiers,
            "multiplicative_total": multiplicative_sum,
            "final_value": final_value
        }
    
    def __repr__(self) -> str:
        name_str = f", name={self._name!r}" if self._name else ""
        return f"ModifiableStat(base={self._base_value}, value={self.get_value()}{name_str})"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典，用于存档。
        
        返回：
            包含属性所有信息的字典
        """
        return {
            "base_value": self._base_value,
            "name": self._name,
            "modifiers": [m.to_dict() for m in self._modifiers]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModifiableStat':
        """
        从字典反序列化创建属性。
        
        参数：
            data: 包含属性信息的字典
            
        返回：
            ModifiableStat 实例
        """
        stat = cls(
            base_value=float(data["base_value"]),
            name=data.get("name")
        )
        for modifier_data in data.get("modifiers", []):
            stat.add_modifier(StatModifier.from_dict(modifier_data))
        return stat
