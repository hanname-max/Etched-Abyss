"""
属性修饰器引擎单元测试

测试 StatModifierEngine 的核心功能，包括：
1. ModifierType 枚举
2. StatModifier 类
3. ModifiableStat 类（动态数值计算）
4. TowerComponent 集成
"""

import pytest
from uuid import UUID

from CoreLogic import (
    ModifierType,
    StatModifier,
    ModifiableStat,
    TowerComponent,
)


class TestModifierType:
    """测试修饰器类型枚举"""

    def test_enum_values(self):
        """测试枚举值定义"""
        assert ModifierType.Additive.value == 1
        assert ModifierType.Multiplicative.value == 2

    def test_enum_names(self):
        """测试枚举名称"""
        assert ModifierType.Additive.name == "Additive"
        assert ModifierType.Multiplicative.name == "Multiplicative"


class TestStatModifier:
    """测试属性修饰器类"""

    def test_creation_basic(self):
        """测试基本创建"""
        modifier = StatModifier(ModifierType.Additive, 10.0)
        assert modifier.modifier_type == ModifierType.Additive
        assert modifier.value == 10.0
        assert modifier.source is None
        assert isinstance(modifier.modifier_id, UUID)

    def test_creation_with_source(self):
        """测试带来源的创建"""
        modifier = StatModifier(
            modifier_type=ModifierType.Multiplicative,
            value=0.2,
            source="狂暴技能"
        )
        assert modifier.modifier_type == ModifierType.Multiplicative
        assert modifier.value == 0.2
        assert modifier.source == "狂暴技能"

    def test_creation_with_custom_id(self):
        """测试带自定义 ID 的创建"""
        custom_id = UUID("12345678-1234-5678-1234-567812345678")
        modifier = StatModifier(
            modifier_type=ModifierType.Additive,
            value=5.0,
            modifier_id=custom_id
        )
        assert modifier.modifier_id == custom_id

    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        original = StatModifier(
            modifier_type=ModifierType.Multiplicative,
            value=0.15,
            source="装备_暴击剑"
        )
        
        data = original.to_dict()
        
        assert data["modifier_type"] == "Multiplicative"
        assert data["value"] == 0.15
        assert data["source"] == "装备_暴击剑"
        assert "modifier_id" in data
        
        restored = StatModifier.from_dict(data)
        
        assert restored.modifier_type == original.modifier_type
        assert restored.value == original.value
        assert restored.source == original.source
        assert restored.modifier_id == original.modifier_id


class TestModifiableStat:
    """测试可修改属性类"""

    def test_creation_basic(self):
        """测试基本创建"""
        stat = ModifiableStat(base_value=100.0)
        assert stat.base_value == 100.0
        assert stat.name is None
        assert stat.get_value() == 100.0

    def test_creation_with_name(self):
        """测试带名称的创建"""
        stat = ModifiableStat(base_value=50.0, name="攻击力")
        assert stat.base_value == 50.0
        assert stat.name == "攻击力"

    def test_base_value_setter(self):
        """测试基础值 setter"""
        stat = ModifiableStat(base_value=100.0)
        assert stat.get_value() == 100.0
        
        stat.base_value = 200.0
        assert stat.base_value == 200.0
        assert stat.get_value() == 200.0

    def test_additive_modifier_single(self):
        """测试单个加法修饰器"""
        stat = ModifiableStat(base_value=100.0)
        modifier = StatModifier(ModifierType.Additive, 20.0)
        
        stat.add_modifier(modifier)
        
        assert stat.get_value() == 120.0

    def test_additive_modifier_multiple(self):
        """测试多个加法修饰器"""
        stat = ModifiableStat(base_value=100.0)
        
        stat.add_modifier(StatModifier(ModifierType.Additive, 20.0))
        stat.add_modifier(StatModifier(ModifierType.Additive, 30.0))
        
        assert stat.get_value() == 150.0

    def test_multiplicative_modifier_single(self):
        """测试单个乘法修饰器"""
        stat = ModifiableStat(base_value=100.0)
        modifier = StatModifier(ModifierType.Multiplicative, 0.2)
        
        stat.add_modifier(modifier)
        
        assert stat.get_value() == 120.0

    def test_multiplicative_modifier_multiple(self):
        """测试多个乘法修饰器（累加系数）"""
        stat = ModifiableStat(base_value=100.0)
        
        stat.add_modifier(StatModifier(ModifierType.Multiplicative, 0.1))
        stat.add_modifier(StatModifier(ModifierType.Multiplicative, 0.2))
        
        assert stat.get_value() == 130.0

    def test_combined_modifiers(self):
        """测试加法和乘法组合（先加后乘规则）"""
        stat = ModifiableStat(base_value=100.0)
        
        stat.add_modifier(StatModifier(ModifierType.Additive, 20.0))
        stat.add_modifier(StatModifier(ModifierType.Additive, 30.0))
        stat.add_modifier(StatModifier(ModifierType.Multiplicative, 0.1))
        stat.add_modifier(StatModifier(ModifierType.Multiplicative, 0.2))
        
        expected = (100 + 20 + 30) * (1 + 0.1 + 0.2)
        assert stat.get_value() == expected
        assert expected == 195.0

    def test_remove_modifier_by_id(self):
        """测试按 ID 移除修饰器"""
        stat = ModifiableStat(base_value=100.0)
        
        modifier1 = StatModifier(ModifierType.Additive, 50.0)
        modifier2 = StatModifier(ModifierType.Additive, 30.0)
        
        stat.add_modifier(modifier1)
        stat.add_modifier(modifier2)
        
        assert stat.get_value() == 180.0
        
        result = stat.remove_modifier(modifier1.modifier_id)
        assert result is True
        assert stat.get_value() == 130.0
        
        invalid_id = UUID("00000000-0000-0000-0000-000000000000")
        result = stat.remove_modifier(invalid_id)
        assert result is False

    def test_remove_all_modifiers(self):
        """测试移除所有修饰器"""
        stat = ModifiableStat(base_value=100.0)
        
        stat.add_modifier(StatModifier(ModifierType.Additive, 50.0))
        stat.add_modifier(StatModifier(ModifierType.Multiplicative, 0.2))
        
        assert stat.get_value() == 180.0
        
        count = stat.remove_all_modifiers()
        assert count == 2
        assert stat.get_value() == 100.0

    def test_remove_modifiers_by_source(self):
        """测试按来源移除修饰器"""
        stat = ModifiableStat(base_value=100.0)
        
        stat.add_modifier(StatModifier(ModifierType.Additive, 20.0, source="药水"))
        stat.add_modifier(StatModifier(ModifierType.Additive, 30.0, source="药水"))
        stat.add_modifier(StatModifier(ModifierType.Multiplicative, 0.5, source="技能"))
        
        assert stat.get_value() == 225.0
        
        count = stat.remove_all_modifiers("药水")
        assert count == 2
        assert stat.get_value() == 150.0
        
        count = stat.remove_all_modifiers("不存在的来源")
        assert count == 0

    def test_get_modifiers(self):
        """测试获取修饰器列表"""
        stat = ModifiableStat(base_value=100.0)
        
        stat.add_modifier(StatModifier(ModifierType.Additive, 10.0))
        stat.add_modifier(StatModifier(ModifierType.Additive, 20.0))
        stat.add_modifier(StatModifier(ModifierType.Multiplicative, 0.1))
        
        all_modifiers = stat.get_modifiers()
        assert len(all_modifiers) == 3
        
        additive_modifiers = stat.get_modifiers(ModifierType.Additive)
        assert len(additive_modifiers) == 2
        
        multiplicative_modifiers = stat.get_modifiers(ModifierType.Multiplicative)
        assert len(multiplicative_modifiers) == 1

    def test_get_breakdown(self):
        """测试获取计算分解信息"""
        stat = ModifiableStat(base_value=100.0, name="攻击力")
        
        stat.add_modifier(StatModifier(ModifierType.Additive, 20.0, source="力量药水"))
        stat.add_modifier(StatModifier(ModifierType.Multiplicative, 0.2, source="狂暴技能"))
        
        breakdown = stat.get_breakdown()
        
        assert breakdown["base_value"] == 100.0
        assert len(breakdown["additive_modifiers"]) == 1
        assert breakdown["additive_total"] == 120.0
        assert len(breakdown["multiplicative_modifiers"]) == 1
        assert breakdown["multiplicative_total"] == 0.2
        assert breakdown["final_value"] == 144.0

    def test_caching(self):
        """测试值缓存机制"""
        stat = ModifiableStat(base_value=100.0)
        
        value1 = stat.get_value()
        value2 = stat.get_value()
        assert value1 == value2
        
        stat.add_modifier(StatModifier(ModifierType.Additive, 50.0))
        value3 = stat.get_value()
        assert value3 == 150.0

    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        original = ModifiableStat(base_value=100.0, name="攻击力")
        original.add_modifier(StatModifier(ModifierType.Additive, 20.0, source="药水"))
        original.add_modifier(StatModifier(ModifierType.Multiplicative, 0.1, source="技能"))
        
        original_value = original.get_value()
        
        data = original.to_dict()
        
        assert data["base_value"] == 100.0
        assert data["name"] == "攻击力"
        assert len(data["modifiers"]) == 2
        
        restored = ModifiableStat.from_dict(data)
        
        assert restored.base_value == original.base_value
        assert restored.name == original.name
        assert restored.get_value() == original_value


class TestTowerComponentIntegration:
    """测试 TowerComponent 与属性修饰器引擎的集成"""

    def test_creation_basic(self):
        """测试基本创建"""
        tower = TowerComponent(
            config_id="tower_arrow_001",
            name="箭塔",
            cost=100,
            damage=20,
            attack_range=3.0,
            attack_speed=1.0
        )
        
        assert tower.damage == 20.0
        assert tower.attack_speed == 1.0
        assert tower.attack_range == 3.0

    def test_damage_stat_access(self):
        """测试获取 damage_stat 并添加修饰器"""
        tower = TowerComponent(
            config_id="tower_arrow_001",
            name="箭塔",
            cost=100,
            damage=20,
            attack_range=3.0,
            attack_speed=1.0
        )
        
        assert tower.damage == 20.0
        
        tower.damage_stat.add_modifier(
            StatModifier(ModifierType.Additive, 10.0, source="力量药水")
        )
        
        assert tower.damage == 30.0

    def test_attack_speed_stat_access(self):
        """测试获取 attack_speed_stat 并添加修饰器"""
        tower = TowerComponent(
            config_id="tower_arrow_001",
            name="箭塔",
            cost=100,
            damage=20,
            attack_range=3.0,
            attack_speed=1.0
        )
        
        assert tower.attack_speed == 1.0
        
        tower.attack_speed_stat.add_modifier(
            StatModifier(ModifierType.Multiplicative, 0.5, source="狂暴技能")
        )
        
        assert tower.attack_speed == 1.5

    def test_attack_cooldown(self):
        """测试 attack_cooldown 便捷属性"""
        tower = TowerComponent(
            config_id="tower_arrow_001",
            name="箭塔",
            cost=100,
            damage=20,
            attack_range=3.0,
            attack_speed=1.0
        )
        
        assert tower.attack_cooldown == 1.0
        
        tower.attack_speed_stat.add_modifier(
            StatModifier(ModifierType.Additive, 1.0)
        )
        
        assert tower.attack_speed == 2.0
        assert tower.attack_cooldown == 0.5

    def test_full_scene(self):
        """测试完整场景：多种修饰器组合"""
        tower = TowerComponent(
            config_id="tower_cannon_001",
            name="炮塔",
            cost=200,
            damage=50,
            attack_range=2.5,
            attack_speed=0.5
        )
        
        assert tower.damage == 50.0
        assert tower.attack_speed == 0.5
        assert tower.attack_cooldown == 2.0
        
        tower.damage_stat.add_modifier(
            StatModifier(ModifierType.Additive, 20.0, source="弹药升级")
        )
        tower.damage_stat.add_modifier(
            StatModifier(ModifierType.Multiplicative, 0.3, source="瞄准系统")
        )
        
        tower.attack_speed_stat.add_modifier(
            StatModifier(ModifierType.Multiplicative, 0.5, source="快速装填")
        )
        
        expected_damage = (50 + 20) * (1 + 0.3)
        assert tower.damage == expected_damage
        
        expected_attack_speed = 0.5 * (1 + 0.5)
        assert tower.attack_speed == expected_attack_speed
        
        expected_cooldown = 1.0 / expected_attack_speed
        assert tower.attack_cooldown == expected_cooldown

    def test_backward_compatibility(self):
        """测试向后兼容性：与现有代码的交互"""
        tower = TowerComponent(
            config_id="tower_arrow_001",
            name="箭塔",
            cost=100,
            damage=20,
            attack_range=3.0,
            attack_speed=1.0,
            description="基础远程防御塔",
            upgrade_ids=["tower_arrow_002"]
        )
        
        assert tower.config_id == "tower_arrow_001"
        assert tower.name == "箭塔"
        assert tower.cost == 100
        assert tower.damage == 20.0
        assert tower.attack_range == 3.0
        assert tower.attack_speed == 1.0
        assert tower.description == "基础远程防御塔"
        assert "tower_arrow_002" in tower.upgrade_ids
