"""
OrganSlotComponent 测试

测试器官插槽组件的功能，包括装备、卸下、合法性校验等。
"""

import pytest
from typing import Optional

from CoreLogic import (
    OrganSlotComponent,
    OrganConfigDTO,
    TowerComponent,
    ServiceLocator,
    EventBus,
)


def _make_organ(organ_id: str = "organ_001", name: str = "测试器官") -> OrganConfigDTO:
    """创建测试用器官配置。"""
    return OrganConfigDTO(
        id=organ_id,
        name=name,
        description="测试用器官",
        attribute_modifiers=[{"attribute": "damage", "value": 0.2}],
    )


class TestOrganSlotComponentInit:
    """初始化测试"""

    def setup_method(self):
        ServiceLocator.reset()
        EventBus.reset()

    def teardown_method(self):
        ServiceLocator.reset()
        EventBus.reset()

    def test_default_slot_count(self):
        """默认 3 个插槽"""
        comp = OrganSlotComponent()
        assert comp.slot_count == 3
        assert len(comp.slots) == 3
        assert all(slot is None for slot in comp.slots)

    def test_custom_slot_count(self):
        """自定义插槽数量"""
        comp = OrganSlotComponent(slot_count=5)
        assert comp.slot_count == 5
        assert len(comp.slots) == 5

    def test_zero_slot_count(self):
        """0 个插槽"""
        comp = OrganSlotComponent(slot_count=0)
        assert comp.slot_count == 0
        assert len(comp.slots) == 0


class TestOrganSlotComponentEquip:
    """装备器官测试"""

    def setup_method(self):
        ServiceLocator.reset()
        EventBus.reset()
        self.comp = OrganSlotComponent(slot_count=3)

    def teardown_method(self):
        ServiceLocator.reset()
        EventBus.reset()

    def test_equip_organ_success(self):
        """装备器官成功"""
        organ = _make_organ()
        assert self.comp.equip_organ(organ, 0) is True
        assert self.comp.slots[0] is organ

    def test_equip_to_occupied_slot_fails(self):
        """已占用插槽装备失败"""
        organ1 = _make_organ("organ_001", "器官1")
        organ2 = _make_organ("organ_002", "器官2")
        self.comp.equip_organ(organ1, 0)
        assert self.comp.equip_organ(organ2, 0) is False
        assert self.comp.slots[0] is organ1

    def test_equip_none_organ_fails(self):
        """装备 None 器官失败"""
        assert self.comp.equip_organ(None, 0) is False

    def test_equip_negative_index_fails(self):
        """负索引装备失败"""
        organ = _make_organ()
        assert self.comp.equip_organ(organ, -1) is False

    def test_equip_out_of_range_index_fails(self):
        """越界索引装备失败"""
        organ = _make_organ()
        assert self.comp.equip_organ(organ, 3) is False

    def test_equip_multiple_organs(self):
        """多个器官装备到不同插槽"""
        organs = [_make_organ(f"organ_{i}", f"器官{i}") for i in range(3)]
        for i, organ in enumerate(organs):
            assert self.comp.equip_organ(organ, i) is True
        for i, organ in enumerate(organs):
            assert self.comp.slots[i] is organ

    def test_equip_does_not_affect_other_slots(self):
        """装备不影响其他插槽"""
        organ = _make_organ()
        self.comp.equip_organ(organ, 1)
        assert self.comp.slots[0] is None
        assert self.comp.slots[1] is organ
        assert self.comp.slots[2] is None


class TestOrganSlotComponentUnequip:
    """卸下器官测试"""

    def setup_method(self):
        ServiceLocator.reset()
        EventBus.reset()
        self.comp = OrganSlotComponent(slot_count=3)

    def teardown_method(self):
        ServiceLocator.reset()
        EventBus.reset()

    def test_unequip_organ_success(self):
        """卸下器官成功"""
        organ = _make_organ()
        self.comp.equip_organ(organ, 0)
        result = self.comp.unequip_organ(0)
        assert result is organ
        assert self.comp.slots[0] is None

    def test_unequip_empty_slot_fails(self):
        """空插槽卸下返回 None"""
        assert self.comp.unequip_organ(0) is None

    def test_unequip_negative_index_fails(self):
        """负索引卸下返回 None"""
        assert self.comp.unequip_organ(-1) is None

    def test_unequip_out_of_range_index_fails(self):
        """越界索引卸下返回 None"""
        assert self.comp.unequip_organ(3) is None

    def test_unequip_all(self):
        """卸下所有器官"""
        organs = [_make_organ(f"organ_{i}", f"器官{i}") for i in range(3)]
        for i, organ in enumerate(organs):
            self.comp.equip_organ(organ, i)
        result = self.comp.unequip_all()
        assert len(result) == 3
        assert all(slot is None for slot in self.comp.slots)

    def test_unequip_all_partial(self):
        """部分插槽有器官时卸下所有"""
        self.comp.equip_organ(_make_organ("organ_0"), 0)
        self.comp.equip_organ(_make_organ("organ_2"), 2)
        result = self.comp.unequip_all()
        assert len(result) == 2
        assert all(slot is None for slot in self.comp.slots)

    def test_unequip_all_empty(self):
        """无器官时卸下所有返回空列表"""
        result = self.comp.unequip_all()
        assert result == []


class TestOrganSlotComponentQuery:
    """查询方法测试"""

    def setup_method(self):
        ServiceLocator.reset()
        EventBus.reset()
        self.comp = OrganSlotComponent(slot_count=3)

    def teardown_method(self):
        ServiceLocator.reset()
        EventBus.reset()

    def test_is_slot_occupied(self):
        """检查插槽占用状态"""
        assert self.comp.is_slot_occupied(0) is False
        self.comp.equip_organ(_make_organ(), 0)
        assert self.comp.is_slot_occupied(0) is True

    def test_is_slot_occupied_out_of_range(self):
        """越界索引抛出 IndexError"""
        with pytest.raises(IndexError):
            self.comp.is_slot_occupied(3)
        with pytest.raises(IndexError):
            self.comp.is_slot_occupied(-1)

    def test_has_empty_slot(self):
        """检查是否有空插槽"""
        assert self.comp.has_empty_slot() is True
        for i in range(3):
            self.comp.equip_organ(_make_organ(f"organ_{i}"), i)
        assert self.comp.has_empty_slot() is False

    def test_get_occupied_slots(self):
        """获取已占用插槽索引"""
        self.comp.equip_organ(_make_organ(), 0)
        self.comp.equip_organ(_make_organ(), 2)
        assert self.comp.get_occupied_slots() == [0, 2]

    def test_get_empty_slots(self):
        """获取空插槽索引"""
        self.comp.equip_organ(_make_organ(), 1)
        assert self.comp.get_empty_slots() == [0, 2]

    def test_get_organ_at(self):
        """获取指定插槽的器官"""
        organ = _make_organ()
        self.comp.equip_organ(organ, 1)
        assert self.comp.get_organ_at(1) is organ
        assert self.comp.get_organ_at(0) is None

    def test_get_organ_at_out_of_range(self):
        """越界索引抛出 IndexError"""
        with pytest.raises(IndexError):
            self.comp.get_organ_at(3)

    def test_get_equipped_organs(self):
        """获取所有已装备器官"""
        organs = [_make_organ(f"organ_{i}") for i in range(2)]
        self.comp.equip_organ(organs[0], 0)
        self.comp.equip_organ(organs[1], 2)
        result = self.comp.get_equipped_organs()
        assert len(result) == 2
        assert organs[0] in result
        assert organs[1] in result


def _make_tower(
    damage: int = 20,
    attack_speed: float = 1.0,
    attack_range: float = 3.0
) -> TowerComponent:
    """创建测试用防御塔组件。"""
    return TowerComponent(
        config_id="tower_test_001",
        name="测试防御塔",
        cost=100,
        damage=damage,
        attack_range=attack_range,
        attack_speed=attack_speed,
    )


def _make_organ_with_modifiers(
    organ_id: str,
    name: str,
    modifiers: list
) -> OrganConfigDTO:
    """创建带属性修饰器的器官配置。"""
    return OrganConfigDTO(
        id=organ_id,
        name=name,
        description=f"{name} - 测试器官",
        attribute_modifiers=modifiers,
    )


class TestOrganSlotComponentStateSync:
    """
    插拔事件与状态同步测试
    
    测试器官插槽与属性计算引擎的联动：
    1. 装备器官时自动应用 StatModifier
    2. 卸下器官时精确移除对应的 StatModifier
    3. 反复插拔后数值完全回退
    """

    def setup_method(self):
        ServiceLocator.reset()
        EventBus.reset()

    def teardown_method(self):
        ServiceLocator.reset()
        EventBus.reset()

    def test_equip_organ_applies_modifier(self):
        """装备器官时自动应用属性修饰器"""
        tower = _make_tower(damage=100)
        organ_slot = OrganSlotComponent(slot_count=3)
        organ_slot.bind_tower(tower)
        
        assert tower.damage == 100.0
        
        organ = _make_organ_with_modifiers(
            "organ_damage_001",
            "攻击强化",
            [{"attribute": "damage", "value": 0.2, "type": "percentage"}]
        )
        
        result = organ_slot.equip_organ(organ, 0)
        assert result is True
        
        assert tower.damage == 120.0

    def test_unequip_organ_removes_modifier_precisely(self):
        """卸下器官时精确移除对应的修饰器"""
        tower = _make_tower(damage=100)
        organ_slot = OrganSlotComponent(slot_count=3)
        organ_slot.bind_tower(tower)
        
        base_damage = tower.damage
        assert base_damage == 100.0
        
        organ = _make_organ_with_modifiers(
            "organ_damage_001",
            "攻击强化",
            [{"attribute": "damage", "value": 0.5, "type": "percentage"}]
        )
        
        organ_slot.equip_organ(organ, 0)
        assert tower.damage == 150.0
        
        unequipped = organ_slot.unequip_organ(0)
        assert unequipped is organ
        
        assert tower.damage == base_damage

    def test_multiple_modifiers_on_same_organ(self):
        """单个器官影响多个属性"""
        tower = _make_tower(damage=100, attack_speed=1.0)
        organ_slot = OrganSlotComponent(slot_count=3)
        organ_slot.bind_tower(tower)
        
        base_damage = tower.damage
        base_speed = tower.attack_speed
        
        organ = _make_organ_with_modifiers(
            "organ_dual_001",
            "双重强化",
            [
                {"attribute": "damage", "value": 50.0, "type": "additive"},
                {"attribute": "attack_speed", "value": 0.5, "type": "percentage"}
            ]
        )
        
        organ_slot.equip_organ(organ, 0)
        
        assert tower.damage == 150.0
        assert tower.attack_speed == 1.5
        
        organ_slot.unequip_organ(0)
        
        assert tower.damage == base_damage
        assert tower.attack_speed == base_speed

    def test_precise_removal_does_not_affect_other_modifiers(self):
        """精确移除只影响目标器官的修饰器，不影响其他来源"""
        from CoreLogic import StatModifier, ModifierType
        
        tower = _make_tower(damage=100)
        organ_slot = OrganSlotComponent(slot_count=3)
        organ_slot.bind_tower(tower)
        
        other_modifier = StatModifier(
            ModifierType.Additive,
            30.0,
            source="其他来源_力量药水"
        )
        tower.damage_stat.add_modifier(other_modifier)
        
        assert tower.damage == 130.0
        
        organ = _make_organ_with_modifiers(
            "organ_damage_001",
            "攻击强化",
            [{"attribute": "damage", "value": 0.2, "type": "percentage"}]
        )
        
        organ_slot.equip_organ(organ, 0)
        
        assert tower.damage == (100 + 30) * 1.2
        
        organ_slot.unequip_organ(0)
        
        assert tower.damage == 130.0

    def test_repeated_equip_unequip_consistency(self):
        """反复插拔同一个器官，数值始终一致"""
        tower = _make_tower(damage=50, attack_speed=1.0)
        organ_slot = OrganSlotComponent(slot_count=3)
        organ_slot.bind_tower(tower)
        
        base_damage = tower.damage
        base_speed = tower.attack_speed
        
        organ = _make_organ_with_modifiers(
            "organ_combo_001",
            "组合强化",
            [
                {"attribute": "damage", "value": 25.0, "type": "additive"},
                {"attribute": "damage", "value": 0.1, "type": "percentage"},
                {"attribute": "attack_speed", "value": 0.3, "type": "percentage"}
            ]
        )
        
        expected_equipped_damage = (50 + 25) * 1.1
        expected_equipped_speed = 1.0 * 1.3
        
        for i in range(5):
            organ_slot.equip_organ(organ, 0)
            assert tower.damage == expected_equipped_damage
            assert tower.attack_speed == expected_equipped_speed
            
            organ_slot.unequip_organ(0)
            assert tower.damage == base_damage
            assert tower.attack_speed == base_speed

    def test_multiple_organs_independent_removal(self):
        """多个器官独立装备和卸下，互不影响"""
        tower = _make_tower(damage=100)
        organ_slot = OrganSlotComponent(slot_count=3)
        organ_slot.bind_tower(tower)
        
        base_damage = tower.damage
        
        organ1 = _make_organ_with_modifiers(
            "organ_add_001",
            "加法强化",
            [{"attribute": "damage", "value": 50.0, "type": "additive"}]
        )
        
        organ2 = _make_organ_with_modifiers(
            "organ_mul_001",
            "乘法强化",
            [{"attribute": "damage", "value": 0.5, "type": "percentage"}]
        )
        
        organ_slot.equip_organ(organ1, 0)
        assert tower.damage == 150.0
        
        organ_slot.equip_organ(organ2, 1)
        assert tower.damage == (100 + 50) * 1.5
        
        organ_slot.unequip_organ(0)
        assert tower.damage == 100 * 1.5
        
        organ_slot.unequip_organ(1)
        assert tower.damage == base_damage

    def test_no_binding_does_not_apply_modifiers(self):
        """未绑定防御塔时，装备器官不影响属性"""
        tower = _make_tower(damage=100)
        organ_slot = OrganSlotComponent(slot_count=3)
        
        base_damage = tower.damage
        
        organ = _make_organ_with_modifiers(
            "organ_damage_001",
            "攻击强化",
            [{"attribute": "damage", "value": 0.5, "type": "percentage"}]
        )
        
        organ_slot.equip_organ(organ, 0)
        
        assert tower.damage == base_damage
        
        organ_slot.bind_tower(tower)
        
        organ_slot.equip_organ(organ, 1)
        assert tower.damage == 150.0

    def test_unequip_all_removes_all_modifiers(self):
        """unequip_all 移除所有已应用的修饰器"""
        tower = _make_tower(damage=100, attack_speed=1.0)
        organ_slot = OrganSlotComponent(slot_count=3)
        organ_slot.bind_tower(tower)
        
        base_damage = tower.damage
        base_speed = tower.attack_speed
        
        organ1 = _make_organ_with_modifiers(
            "organ_damage_001",
            "攻击强化",
            [{"attribute": "damage", "value": 50.0, "type": "additive"}]
        )
        
        organ2 = _make_organ_with_modifiers(
            "organ_speed_001",
            "速度强化",
            [{"attribute": "attack_speed", "value": 1.0, "type": "additive"}]
        )
        
        organ_slot.equip_organ(organ1, 0)
        organ_slot.equip_organ(organ2, 2)
        
        assert tower.damage == 150.0
        assert tower.attack_speed == 2.0
        
        unequipped = organ_slot.unequip_all()
        assert len(unequipped) == 2
        
        assert tower.damage == base_damage
        assert tower.attack_speed == base_speed

    def test_get_applied_modifier_count(self):
        """get_applied_modifier_count 返回正确的修饰器数量"""
        tower = _make_tower(damage=100)
        organ_slot = OrganSlotComponent(slot_count=3)
        organ_slot.bind_tower(tower)
        
        assert organ_slot.get_applied_modifier_count() == 0
        
        organ_single = _make_organ_with_modifiers(
            "organ_single",
            "单属性",
            [{"attribute": "damage", "value": 10.0, "type": "additive"}]
        )
        
        organ_dual = _make_organ_with_modifiers(
            "organ_dual",
            "双属性",
            [
                {"attribute": "damage", "value": 20.0, "type": "additive"},
                {"attribute": "attack_speed", "value": 0.1, "type": "percentage"}
            ]
        )
        
        organ_slot.equip_organ(organ_single, 0)
        assert organ_slot.get_applied_modifier_count() == 1
        
        organ_slot.equip_organ(organ_dual, 1)
        assert organ_slot.get_applied_modifier_count() == 3
        
        organ_slot.unequip_organ(0)
        assert organ_slot.get_applied_modifier_count() == 2
        
        organ_slot.unequip_all()
        assert organ_slot.get_applied_modifier_count() == 0
