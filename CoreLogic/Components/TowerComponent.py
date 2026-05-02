"""
防御塔组件

TowerComponent 用于记录防御塔实体的基础属性。

============================================================================
【架构规范强制声明】
============================================================================

这是一个纯粹的数据容器，不包含任何业务逻辑。
所有防御塔相关的逻辑（如攻击、升级、卖出）都应该在 System 中实现。
============================================================================
"""

from dataclasses import dataclass, field, InitVar
from typing import List, Optional

from CoreLogic.Utils.StatModifierEngine import ModifiableStat


@dataclass
class TowerComponent:
    """
    防御塔组件，记录防御塔实体的基础属性。
    
    存储从 TowerConfigDTO 复制的配置属性，供战斗系统使用。
    
    属性：
        config_id: 防御塔配置的唯一标识符
        name: 防御塔的可读名称
        cost: 建造费用
        damage: 最终伤害值（自动计算所有修饰器后的结果）
        attack_range: 攻击范围（单位格数）
        attack_speed: 最终攻击速度（自动计算所有修饰器后的结果，次/秒）
        description: 防御塔的描述文本
        upgrade_ids: 可升级到的后续防御塔 ID 列表
        
    动态属性修饰：
        damage_stat: ModifiableStat 实例，用于添加/移除伤害修饰器
        attack_speed_stat: ModifiableStat 实例，用于添加/移除攻击速度修饰器
        
    使用示例：
        # 创建防御塔实体并添加组件
        entity = BaseEntity(entity_id=1)
        entity.add_component(TransformComponent(x=5.0, y=3.0))
        tower_comp = TowerComponent(
            config_id="tower_arrow_001",
            name="箭塔",
            cost=100,
            damage=20,
            attack_range=3.0,
            attack_speed=1.0,
            description="基础远程防御塔",
            upgrade_ids=["tower_arrow_002"]
        )
        entity.add_component(tower_comp)
        
        # 添加伤害修饰器（+10 伤害）
        from CoreLogic.Utils import ModifierType, StatModifier
        buff = StatModifier(ModifierType.Additive, 10.0, source="力量药水")
        tower_comp.damage_stat.add_modifier(buff)
        
        # 伤害会自动更新
        print(tower_comp.damage)  # 输出 30.0
    """
    
    config_id: str
    name: str
    cost: int
    attack_range: float
    description: str = ""
    upgrade_ids: List[str] = None
    
    damage: InitVar[int] = 0
    attack_speed: InitVar[float] = 0.0
    
    _damage_stat: ModifiableStat = field(init=False, repr=False)
    _attack_speed_stat: ModifiableStat = field(init=False, repr=False)
    
    def __post_init__(self, damage: int, attack_speed: float) -> None:
        """
        初始化后处理，将数值转换为 ModifiableStat。
        
        参数：
            damage: 基础伤害值
            attack_speed: 基础攻击速度
        """
        self._damage_stat = ModifiableStat(base_value=float(damage), name="伤害")
        self._attack_speed_stat = ModifiableStat(base_value=attack_speed, name="攻击速度")
    
    @property
    def damage(self) -> float:
        """
        获取最终伤害值（自动计算所有修饰器）。
        
        返回：
            计算后的伤害值
        """
        return self._damage_stat.get_value()
    
    @property
    def attack_speed(self) -> float:
        """
        获取最终攻击速度（自动计算所有修饰器）。
        
        返回：
            计算后的攻击速度（次/秒）
        """
        return self._attack_speed_stat.get_value()
    
    @property
    def damage_stat(self) -> ModifiableStat:
        """
        获取伤害属性的 ModifiableStat 实例，用于添加/移除修饰器。
        
        返回：
            ModifiableStat 实例
        """
        return self._damage_stat
    
    @property
    def attack_speed_stat(self) -> ModifiableStat:
        """
        获取攻击速度属性的 ModifiableStat 实例，用于添加/移除修饰器。
        
        返回：
            ModifiableStat 实例
        """
        return self._attack_speed_stat
    
    @property
    def attack_cooldown(self) -> float:
        """
        获取攻击冷却时间（攻击速度的倒数）。
        
        这是一个便捷属性，用于计算两次攻击之间的间隔时间。
        
        返回：
            冷却时间（秒），如果攻击速度为 0 则返回无穷大
        """
        speed = self._attack_speed_stat.get_value()
        if speed <= 0:
            return float('inf')
        return 1.0 / speed
