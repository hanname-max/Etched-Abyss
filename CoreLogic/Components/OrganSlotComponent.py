"""
器官插槽组件

OrganSlotComponent 用于管理防御塔的器官插槽系统。

============================================================================
【架构说明】
============================================================================

此组件与 MovementComponent 类似，作为架构规范的例外，
包含业务逻辑方法（EquipOrgan 和 UnequipOrgan）用于管理器官的插拔操作。

使用方式：
    organ_slot = OrganSlotComponent(slot_count=3)
    organ_slot.bind_tower(tower_component)
    organ_slot.equip_organ(organ_config, 0)
    organ_slot.unequip_organ(0)

============================================================================
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from CoreLogic.DTOs.OrganConfigDTO import OrganConfigDTO
from CoreLogic.Core.ServiceLocator import try_get_service
from CoreLogic.Interfaces.IGameLogger import IGameLogger
from CoreLogic.Utils.StatModifierEngine import (
    ModifierType,
    StatModifier,
    ModifiableStat,
)


@dataclass
class OrganSlotComponent:
    """
    器官插槽组件，管理防御塔的器官插槽系统。
    
    防御塔可以装备多个器官来增强属性。此组件负责管理这些插槽，
    提供装备和卸下器官的接口，并进行合法性校验。
    
    属性：
        slot_count: 插槽数量，默认为 3
        slots: 插槽列表，每个元素是一个 OrganConfigDTO 或 None
        _logger: 缓存的日志器引用，避免重复从 ServiceLocator 获取
        _tower: 绑定的防御塔组件引用，用于联动属性修饰器
        _slot_modifiers: 追踪每个插槽应用的修饰器，格式为 {slot_index: [(attribute_name, modifier_id), ...]}
    
    使用示例：
        # 创建防御塔和器官插槽组件
        tower = TowerComponent(
            config_id="tower_arrow_001",
            name="箭塔",
            cost=100,
            damage=20,
            attack_range=3.0,
            attack_speed=1.0
        )
        organ_slot = OrganSlotComponent(slot_count=3)
        organ_slot.bind_tower(tower)
        
        # 创建带属性加成的器官
        organ_config = OrganConfigDTO(
            id="organ_heart_001",
            name="强化之心",
            description="增加攻击力 20%",
            attribute_modifiers=[
                {"attribute": "damage", "value": 0.2, "type": "percentage"},
                {"attribute": "attack_speed", "value": 0.1, "type": "percentage"}
            ]
        )
        
        # 装备器官（自动应用属性修饰）
        organ_slot.equip_organ(organ_config, 0)
        print(f"装备后伤害: {tower.damage}")  # 20 * 1.2 = 24
        
        # 卸下器官（精确移除修饰器，属性回退）
        organ_slot.unequip_organ(0)
        print(f"卸下后伤害: {tower.damage}")  # 回退到 20
    """
    
    slot_count: int = 3
    slots: List[Optional[OrganConfigDTO]] = field(default_factory=list)
    _logger: Optional[IGameLogger] = field(default=None, repr=False)
    _tower: Optional[Any] = field(default=None, repr=False)
    _slot_modifiers: Dict[int, List[Tuple[str, UUID]]] = field(default_factory=dict, repr=False)
    
    def __post_init__(self) -> None:
        """
        初始化后处理。
        确保 slots 列表的大小与 slot_count 一致，初始化为 None。
        """
        if not self.slots or len(self.slots) != self.slot_count:
            self.slots = [None] * self.slot_count
        if self._slot_modifiers is None:
            self._slot_modifiers = {}
    
    def _get_logger(self) -> Optional[IGameLogger]:
        """
        获取日志器。
        如果缓存的日志器为 None，则尝试从 ServiceLocator 获取。
        """
        if self._logger is None:
            self._logger = try_get_service(IGameLogger)
        return self._logger
    
    def _log_info(self, message: str, **kwargs) -> None:
        """
        记录信息级别日志。
        """
        logger = self._get_logger()
        if logger is not None:
            logger.info(message, **kwargs)
    
    def _log_warn(self, message: str, **kwargs) -> None:
        """
        记录警告级别日志。
        """
        logger = self._get_logger()
        if logger is not None:
            logger.warn(message, **kwargs)
    
    def _is_valid_index(self, slot_index: int) -> bool:
        """
        检查插槽索引是否有效。
        
        参数：
            slot_index: 要检查的插槽索引
            
        返回：
            True 如果索引在有效范围内（0 <= slot_index < slot_count）
        """
        return 0 <= slot_index < self.slot_count
    
    def bind_tower(self, tower_component: Any) -> None:
        """
        绑定防御塔组件。
        
        将器官插槽组件与特定的防御塔组件关联，
        以便在装备/卸下器官时自动应用/移除属性修饰器。
        
        参数：
            tower_component: TowerComponent 实例
        """
        self._tower = tower_component
        self._log_info(
            "OrganSlotComponent: 绑定防御塔组件",
            tower_name=getattr(tower_component, 'name', 'unknown')
        )
    
    def unbind_tower(self) -> None:
        """
        解绑防御塔组件。

        解绑前会自动卸下所有已装备的器官，确保修饰器被正确移除，
        防止脏数据残留。
        """
        if self._tower is not None:
            self.unequip_all()
            self._log_info("OrganSlotComponent: 解绑防御塔组件")
            self._tower = None
    
    def _parse_attribute_modifiers(
        self, 
        organ: OrganConfigDTO
    ) -> List[Tuple[str, StatModifier]]:
        """
        解析器官配置中的 attribute_modifiers，转换为 StatModifier 列表。
        
        参数：
            organ: 器官配置 DTO
            
        返回：
            列表，每个元素为 (attribute_name, StatModifier) 元组
            
        修饰器类型映射：
            - "percentage" 或 "%": ModifierType.Multiplicative
            - "additive" 或其他: ModifierType.Additive
        """
        result: List[Tuple[str, StatModifier]] = []
        
        for modifier_data in organ.attribute_modifiers:
            attribute_name = modifier_data.get("attribute", "")
            value = modifier_data.get("value", 0.0)
            modifier_type_str = modifier_data.get("type", "additive")
            
            if not attribute_name:
                self._log_warn(
                    "OrganSlotComponent: 跳过无效的属性修饰器（缺少 attribute）",
                    organ_id=organ.id
                )
                continue
            
            if modifier_type_str in ("percentage", "%", "multiplicative"):
                modifier_type = ModifierType.Multiplicative
            else:
                modifier_type = ModifierType.Additive
            
            source = f"organ_{organ.id}"
            modifier = StatModifier(
                modifier_type=modifier_type,
                value=float(value),
                source=source
            )
            
            result.append((attribute_name, modifier))
        
        return result
    
    def _get_stat_for_attribute(self, attribute_name: str) -> Optional[ModifiableStat]:
        """
        根据属性名获取对应的 ModifiableStat 实例。
        
        参数：
            attribute_name: 属性名，如 "damage", "attack_speed"
            
        返回：
            对应的 ModifiableStat 实例，如果未找到或未绑定塔则返回 None
        """
        if self._tower is None:
            return None
        
        attribute_map = {
            "damage": "damage_stat",
            "attack_speed": "attack_speed_stat",
        }
        
        stat_property_name = attribute_map.get(attribute_name.lower())
        if stat_property_name is None:
            self._log_warn(
                "OrganSlotComponent: 未知的属性名",
                attribute_name=attribute_name
            )
            return None
        
        stat = getattr(self._tower, stat_property_name, None)
        if stat is None:
            self._log_warn(
                "OrganSlotComponent: 防御塔不支持该属性",
                attribute_name=attribute_name,
                stat_property_name=stat_property_name
            )
            return None
        
        return stat
    
    def _apply_modifiers_to_slot(
        self, 
        slot_index: int, 
        modifiers: List[Tuple[str, StatModifier]]
    ) -> None:
        """
        应用修饰器到指定插槽，并记录 modifier_id 以便精确移除。
        
        参数：
            slot_index: 插槽索引
            modifiers: 要应用的修饰器列表，格式为 [(attribute_name, StatModifier), ...]
        """
        applied_records: List[Tuple[str, UUID]] = []
        
        for attribute_name, modifier in modifiers:
            stat = self._get_stat_for_attribute(attribute_name)
            if stat is not None:
                stat.add_modifier(modifier)
                applied_records.append((attribute_name, modifier.modifier_id))
                self._log_info(
                    "OrganSlotComponent: 应用属性修饰器",
                    attribute=attribute_name,
                    modifier_type=modifier.modifier_type.name,
                    value=modifier.value,
                    source=modifier.source,
                    modifier_id=str(modifier.modifier_id)
                )
        
        if applied_records:
            self._slot_modifiers[slot_index] = applied_records
    
    def _remove_modifiers_from_slot(self, slot_index: int) -> int:
        """
        从指定插槽精确移除所有已应用的修饰器。
        
        此方法使用记录的 modifier_id 进行精确移除，确保只移除
        该器官添加的修饰器，不会影响其他来源的修饰器。
        
        参数：
            slot_index: 插槽索引
            
        返回：
            成功移除的修饰器数量
        """
        if slot_index not in self._slot_modifiers:
            return 0
        
        records = self._slot_modifiers.pop(slot_index, [])
        removed_count = 0
        
        for attribute_name, modifier_id in records:
            stat = self._get_stat_for_attribute(attribute_name)
            if stat is not None:
                success = stat.remove_modifier(modifier_id)
                if success:
                    removed_count += 1
                    self._log_info(
                        "OrganSlotComponent: 移除属性修饰器",
                        attribute=attribute_name,
                        modifier_id=str(modifier_id)
                    )
        
        return removed_count
    
    def is_slot_occupied(self, slot_index: int) -> bool:
        """
        检查指定插槽是否已被占用。
        
        参数：
            slot_index: 插槽索引
            
        返回：
            True 如果插槽已被占用（有器官装备），False 否则
            
        异常：
            IndexError: 如果插槽索引越界
        """
        if not self._is_valid_index(slot_index):
            raise IndexError(f"插槽索引越界: {slot_index}，有效范围: 0-{self.slot_count - 1}")
        
        return self.slots[slot_index] is not None
    
    def has_empty_slot(self) -> bool:
        """
        检查是否有空插槽。
        
        返回：
            True 如果存在至少一个空插槽，False 否则
        """
        return any(slot is None for slot in self.slots)
    
    def get_occupied_slots(self) -> List[int]:
        """
        获取所有已占用的插槽索引列表。
        
        返回：
            已占用插槽的索引列表
        """
        return [i for i, slot in enumerate(self.slots) if slot is not None]
    
    def get_empty_slots(self) -> List[int]:
        """
        获取所有空插槽的索引列表。
        
        返回：
            空插槽的索引列表
        """
        return [i for i, slot in enumerate(self.slots) if slot is None]
    
    def get_organ_at(self, slot_index: int) -> Optional[OrganConfigDTO]:
        """
        获取指定插槽的器官。
        
        参数：
            slot_index: 插槽索引
            
        返回：
            指定插槽的 OrganConfigDTO，如果插槽为空则返回 None
            
        异常：
            IndexError: 如果插槽索引越界
        """
        if not self._is_valid_index(slot_index):
            raise IndexError(f"插槽索引越界: {slot_index}，有效范围: 0-{self.slot_count - 1}")
        
        return self.slots[slot_index]
    
    def equip_organ(self, organ: OrganConfigDTO, slot_index: int) -> bool:
        """
        装备器官到指定插槽。
        
        如果已绑定防御塔组件，会自动解析器官配置中的 attribute_modifiers，
        创建 StatModifier 并应用到对应的属性上。
        
        执行以下合法性校验：
        1. 插槽索引必须在有效范围内
        2. 目标插槽必须为空
        3. 不能装备 None 器官
        
        参数：
            organ: 要装备的器官配置 DTO
            slot_index: 目标插槽索引
            
        返回：
            True 如果装备成功，False 否则（插槽已被占用或索引无效）
        """
        if organ is None:
            self._log_warn("OrganSlotComponent: 尝试装备 None 器官")
            return False
        
        if not self._is_valid_index(slot_index):
            self._log_warn(
                "OrganSlotComponent: 插槽索引越界",
                slot_index=slot_index,
                valid_range=f"0-{self.slot_count - 1}"
            )
            return False
        
        if self.slots[slot_index] is not None:
            self._log_warn(
                "OrganSlotComponent: 目标插槽已被占用，无法装备",
                slot_index=slot_index,
                occupied_organ=self.slots[slot_index].id
            )
            return False
        
        self.slots[slot_index] = organ
        
        if self._tower is not None:
            modifiers = self._parse_attribute_modifiers(organ)
            if modifiers:
                self._apply_modifiers_to_slot(slot_index, modifiers)
        
        self._log_info(
            "OrganSlotComponent: 器官装备成功",
            organ_id=organ.id,
            organ_name=organ.name,
            slot_index=slot_index
        )
        
        return True
    
    def unequip_organ(self, slot_index: int) -> Optional[OrganConfigDTO]:
        """
        从指定插槽卸下器官。
        
        如果已绑定防御塔组件，会精确移除该器官添加的所有 StatModifier。
        此方法使用记录的 modifier_id 进行精确移除，确保只移除该器官
        添加的修饰器，不会影响其他来源的修饰器。
        
        执行以下合法性校验：
        1. 插槽索引必须在有效范围内
        
        参数：
            slot_index: 目标插槽索引
            
        返回：
            被卸下的器官配置 DTO，如果插槽为空则返回 None
        """
        if not self._is_valid_index(slot_index):
            self._log_warn(
                "OrganSlotComponent: 插槽索引越界",
                slot_index=slot_index,
                valid_range=f"0-{self.slot_count - 1}"
            )
            return None
        
        organ = self.slots[slot_index]
        
        if organ is None:
            self._log_warn(
                "OrganSlotComponent: 目标插槽为空，无法卸下",
                slot_index=slot_index
            )
            return None
        
        self.slots[slot_index] = None
        
        if self._tower is not None:
            removed_count = self._remove_modifiers_from_slot(slot_index)
            self._log_info(
                "OrganSlotComponent: 已移除属性修饰器",
                organ_id=organ.id,
                removed_count=removed_count
            )
        
        self._log_info(
            "OrganSlotComponent: 器官卸下成功",
            organ_id=organ.id,
            organ_name=organ.name,
            slot_index=slot_index
        )
        
        return organ
    
    def unequip_all(self) -> List[OrganConfigDTO]:
        """
        卸下所有已装备的器官。
        
        返回：
            所有被卸下的器官列表
        """
        unequipped_organs = []
        
        for i in range(self.slot_count):
            if self.slots[i] is not None:
                organ = self.unequip_organ(i)
                if organ is not None:
                    unequipped_organs.append(organ)
        
        return unequipped_organs
    
    def get_equipped_organs(self) -> List[OrganConfigDTO]:
        """
        获取所有已装备的器官列表。
        
        返回：
            所有已装备的器官配置 DTO 列表
        """
        return [slot for slot in self.slots if slot is not None]
    
    def get_applied_modifier_count(self) -> int:
        """
        获取当前已应用的修饰器总数（用于调试和验证）。
        
        返回：
            所有插槽中已记录的修饰器数量
        """
        total = 0
        for records in self._slot_modifiers.values():
            total += len(records)
        return total
