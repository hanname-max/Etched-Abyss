"""
WaveManager 测试用例

测试 WaveManager 波次管理器的功能，包括：
1. IoC 容器依赖获取
2. 敌人生成与组件挂载
3. A* 寻路路径计算
4. 波次时间调度
"""

import pytest
from typing import List, Tuple

from CoreLogic import (
    WaveManager,
    SpawnTask,
    EntityManager,
    MockDataLoader,
    GridMap,
    Pathfinder,
    TransformComponent,
    HealthComponent,
    MovementComponent,
    ServiceLocator,
    EventBus,
    register_service,
    get_service,
)


class TestWaveManagerBasics:
    """WaveManager 基本功能测试"""

    def setup_method(self):
        """每个测试方法前的准备工作。"""
        ServiceLocator.reset()
        EventBus.reset()
        self.wave_manager = WaveManager()

    def teardown_method(self):
        """每个测试方法后的清理工作。"""
        ServiceLocator.reset()
        EventBus.reset()

    def test_create_wave_manager(self):
        """测试创建 WaveManager 实例。"""
        wm = WaveManager()
        assert wm is not None
        assert wm.is_running is False
        assert wm.current_wave_id is None
        assert wm.spawned_count == 0
        assert wm.total_to_spawn == 0

    def test_set_spawn_point(self):
        """测试设置生成点坐标。"""
        self.wave_manager.set_spawn_point(5, 3)
        assert self.wave_manager.spawn_point == (5, 3)

    def test_set_end_point(self):
        """测试设置终点坐标。"""
        self.wave_manager.set_end_point(10, 8)
        assert self.wave_manager.end_point == (10, 8)

    def test_default_spawn_and_end_points(self):
        """测试默认的生成点和终点坐标。"""
        assert self.wave_manager.spawn_point == (0, 0)
        assert self.wave_manager.end_point == (0, 0)

    def test_reset(self):
        """测试重置 WaveManager 状态。"""
        self.wave_manager.set_spawn_point(5, 5)
        self.wave_manager.set_end_point(10, 10)
        
        self.wave_manager.reset()
        
        assert self.wave_manager.spawn_point == (0, 0)
        assert self.wave_manager.end_point == (0, 0)
        assert self.wave_manager.is_running is False
        assert self.wave_manager.spawned_count == 0


class TestWaveManagerIoC:
    """WaveManager IoC 容器依赖获取测试"""

    def setup_method(self):
        """每个测试方法前的准备工作。"""
        ServiceLocator.reset()
        EventBus.reset()

    def teardown_method(self):
        """每个测试方法后的清理工作。"""
        ServiceLocator.reset()
        EventBus.reset()

    def test_get_entity_manager_from_ioc(self):
        """测试从 IoC 容器获取 EntityManager。"""
        em = EntityManager()
        register_service(EntityManager, em)
        
        wm = WaveManager()
        
        retrieved = wm._get_entity_manager()
        assert retrieved is em

    def test_get_data_loader_from_ioc(self):
        """测试从 IoC 容器获取 IDataLoader。"""
        loader = MockDataLoader()
        from CoreLogic.Interfaces.IDataLoader import IDataLoader
        register_service(IDataLoader, loader)
        
        wm = WaveManager()
        
        retrieved = wm._get_data_loader()
        assert retrieved is loader

    def test_get_pathfinder_creates_new_if_not_registered(self):
        """测试如果 Pathfinder 未注册，会创建新实例。"""
        wm = WaveManager()
        
        pf = wm._get_pathfinder()
        assert pf is not None
        assert isinstance(pf, Pathfinder)

    def test_get_grid_map_from_ioc(self):
        """测试从 IoC 容器获取 GridMap。"""
        grid_map = GridMap(width=10, height=10)
        register_service(GridMap, grid_map)
        
        wm = WaveManager()
        
        retrieved = wm._get_grid_map()
        assert retrieved is grid_map

    def test_manual_dependency_injection(self):
        """测试手动注入依赖（不通过 IoC）。"""
        em = EntityManager()
        loader = MockDataLoader()
        pf = Pathfinder()
        grid_map = GridMap(width=10, height=10)
        
        wm = WaveManager()
        wm.set_entity_manager(em)
        wm.set_data_loader(loader)
        wm.set_pathfinder(pf)
        wm.set_grid_map(grid_map)
        
        assert wm._get_entity_manager() is em
        assert wm._get_data_loader() is loader
        assert wm._get_pathfinder() is pf
        assert wm._get_grid_map() is grid_map


class TestWaveManagerEnemySpawning:
    """WaveManager 敌人生成测试"""

    def setup_method(self):
        """每个测试方法前的准备工作。"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.entity_manager = EntityManager()
        self.data_loader = MockDataLoader()
        self.grid_map = GridMap(width=10, height=10)
        
        from CoreLogic.Interfaces.IDataLoader import IDataLoader
        register_service(EntityManager, self.entity_manager)
        register_service(IDataLoader, self.data_loader)
        register_service(GridMap, self.grid_map)
        
        self.wave_manager = WaveManager()
        self.wave_manager.set_spawn_point(0, 5)
        self.wave_manager.set_end_point(9, 5)

    def teardown_method(self):
        """每个测试方法后的清理工作。"""
        ServiceLocator.reset()
        EventBus.reset()

    def test_spawn_enemy_at_creates_entity(self):
        """测试 spawn_enemy_at 方法创建实体。"""
        initial_count = self.entity_manager.get_entity_count()
        
        success = self.wave_manager.spawn_enemy_at("enemy_basic_001", 0, 5)
        
        assert success is True
        assert self.entity_manager.get_entity_count() == initial_count + 1

    def test_spawned_enemy_has_transform_component(self):
        """测试生成的敌人有 TransformComponent。"""
        self.wave_manager.spawn_enemy_at("enemy_basic_001", 2, 3)
        
        entities = self.entity_manager.get_all_entities()
        assert len(entities) == 1
        
        entity = entities[0]
        transform = entity.get_component(TransformComponent)
        assert transform is not None
        assert transform.x == 2.0
        assert transform.y == 3.0

    def test_spawned_enemy_has_health_component(self):
        """测试生成的敌人有 HealthComponent。"""
        self.wave_manager.spawn_enemy_at("enemy_basic_001", 0, 0)
        
        entities = self.entity_manager.get_all_entities()
        entity = entities[0]
        health = entity.get_component(HealthComponent)
        
        assert health is not None
        assert health.max_health == 100.0
        assert health.current_health == 100.0

    def test_spawned_enemy_has_movement_component(self):
        """测试生成的敌人有 MovementComponent。"""
        self.wave_manager.spawn_enemy_at("enemy_basic_001", 0, 5)
        
        entities = self.entity_manager.get_all_entities()
        entity = entities[0]
        movement = entity.get_component(MovementComponent)
        
        assert movement is not None
        assert movement.speed == 1.5

    def test_spawned_enemy_has_path_calculated(self):
        """测试生成的敌人有计算好的路径。
        
        注意：路径点不包含起点（因为敌人已经在起点），
        第一个路径点是敌人需要移动到的下一个位置。
        """
        self.wave_manager.spawn_enemy_at("enemy_basic_001", 0, 5)
        
        entities = self.entity_manager.get_all_entities()
        entity = entities[0]
        movement = entity.get_component(MovementComponent)
        
        assert movement.has_waypoints is True
        assert len(movement.waypoints) > 0
        
        path_list = list(movement.waypoints)
        assert path_list[0] == (1.0, 5.0)
        assert path_list[-1] == (9.0, 5.0)

    def test_spawn_enemy_with_invalid_id_returns_false(self):
        """测试使用无效的敌人 ID 返回 False。"""
        success = self.wave_manager.spawn_enemy_at("invalid_enemy_id", 0, 0)
        assert success is False
        assert self.entity_manager.get_entity_count() == 0

    def test_spawn_enemy_without_grid_map_returns_false(self):
        """测试没有 GridMap 时返回 False。"""
        ServiceLocator.reset()
        
        wm = WaveManager()
        wm.set_entity_manager(self.entity_manager)
        wm.set_data_loader(self.data_loader)
        
        success = wm.spawn_enemy_at("enemy_basic_001", 0, 0)
        assert success is False


class TestWaveManagerWaveScheduling:
    """WaveManager 波次调度测试"""

    def setup_method(self):
        """每个测试方法前的准备工作。"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.entity_manager = EntityManager()
        self.data_loader = MockDataLoader()
        self.grid_map = GridMap(width=10, height=10)
        
        from CoreLogic.Interfaces.IDataLoader import IDataLoader
        register_service(EntityManager, self.entity_manager)
        register_service(IDataLoader, self.data_loader)
        register_service(GridMap, self.grid_map)
        
        self.wave_manager = WaveManager()
        self.wave_manager.set_spawn_point(0, 5)
        self.wave_manager.set_end_point(9, 5)

    def teardown_method(self):
        """每个测试方法后的清理工作。"""
        ServiceLocator.reset()
        EventBus.reset()

    def test_start_wave_with_valid_id(self):
        """测试使用有效的波次 ID 开始波次。"""
        success = self.wave_manager.start_wave("wave_01_001")
        
        assert success is True
        assert self.wave_manager.is_running is True
        assert self.wave_manager.current_wave_id == "wave_01_001"
        assert self.wave_manager.total_to_spawn == 5

    def test_start_wave_with_invalid_id_returns_false(self):
        """测试使用无效的波次 ID 返回 False。"""
        success = self.wave_manager.start_wave("invalid_wave_id")
        
        assert success is False
        assert self.wave_manager.is_running is False

    def test_cannot_start_wave_while_another_is_running(self):
        """测试不能在一个波次运行时开始另一个。"""
        self.wave_manager.start_wave("wave_01_001")
        
        success = self.wave_manager.start_wave("wave_01_002")
        
        assert success is False

    def test_stop_wave(self):
        """测试停止波次。"""
        self.wave_manager.start_wave("wave_01_001")
        assert self.wave_manager.is_running is True
        
        self.wave_manager.stop_wave()
        
        assert self.wave_manager.is_running is False
        assert self.wave_manager.current_wave_id is None

    def test_tick_spawns_enemies_over_time(self):
        """测试 tick 方法随时间生成敌人。"""
        self.wave_manager.start_wave("wave_01_001")
        
        assert self.wave_manager.spawned_count == 0
        
        self.wave_manager.tick(delta=0.5)
        
        assert self.wave_manager.spawned_count == 1
        assert self.entity_manager.get_entity_count() == 1
        
        self.wave_manager.tick(delta=1.5)
        assert self.wave_manager.spawned_count == 2

    def test_wave_completes_after_all_spawns(self):
        """测试所有敌人生成后波次完成。"""
        self.wave_manager.start_wave("wave_01_001")
        
        for _ in range(10):
            self.wave_manager.tick(delta=1.0)
        
        assert self.wave_manager.is_running is False
        assert self.wave_manager.spawned_count == 5
        assert self.entity_manager.get_entity_count() == 5

    def test_wave_with_multiple_spawn_configs(self):
        """测试有多个敌人生成配置的波次。"""
        self.wave_manager.start_wave("wave_01_002")
        assert self.wave_manager.total_to_spawn == 11
        
        for _ in range(20):
            self.wave_manager.tick(delta=1.0)
        
        assert self.wave_manager.spawned_count == 11


class TestWaveManagerIntegration:
    """WaveManager 集成测试（与 EntityManager、Pathfinder 配合）"""

    def setup_method(self):
        """每个测试方法前的准备工作。"""
        ServiceLocator.reset()
        EventBus.reset()
        
        self.entity_manager = EntityManager()
        self.data_loader = MockDataLoader()
        self.grid_map = GridMap(width=10, height=10)
        
        from CoreLogic.Interfaces.IDataLoader import IDataLoader
        register_service(EntityManager, self.entity_manager)
        register_service(IDataLoader, self.data_loader)
        register_service(GridMap, self.grid_map)
        
        self.wave_manager = WaveManager()
        self.wave_manager.set_spawn_point(0, 5)
        self.wave_manager.set_end_point(9, 5)

    def teardown_method(self):
        """每个测试方法后的清理工作。"""
        ServiceLocator.reset()
        EventBus.reset()

    def test_enemy_moves_along_path_in_entity_manager(self):
        """测试敌人在 EntityManager 中沿着路径移动。"""
        self.wave_manager.spawn_enemy_at("enemy_basic_001", 0, 5)
        
        entities = self.entity_manager.get_all_entities()
        assert len(entities) == 1
        
        entity = entities[0]
        transform = entity.get_component(TransformComponent)
        movement = entity.get_component(MovementComponent)
        
        initial_x = transform.x
        assert initial_x == 0.0
        
        self.entity_manager.tick(delta=1.0)
        
        assert transform.x > initial_x
        assert movement.reached_end is False

    def test_enemy_reaches_end_after_full_path(self):
        """测试敌人走完完整路径后到达终点。"""
        self.wave_manager.spawn_enemy_at("enemy_fast_001", 0, 5)
        
        entities = self.entity_manager.get_all_entities()
        entity = entities[0]
        transform = entity.get_component(TransformComponent)
        movement = entity.get_component(MovementComponent)
        
        for _ in range(50):
            self.entity_manager.tick(delta=0.5)
            if movement.reached_end:
                break
        
        assert movement.reached_end is True
        assert transform.x == 9.0
        assert transform.y == 5.0

    def test_pathfinding_around_obstacles(self):
        """测试绕开障碍物的寻路。
        
        注意：路径点不包含起点（因为敌人已经在起点）。
        """
        for y in range(10):
            if y != 0:
                self.grid_map.set_walkable(5, y, False)
        
        self.wave_manager.spawn_enemy_at("enemy_basic_001", 0, 5)
        
        entities = self.entity_manager.get_all_entities()
        entity = entities[0]
        movement = entity.get_component(MovementComponent)
        
        path = list(movement.waypoints)
        
        blocked_coords = [(5, y) for y in range(1, 10)]
        for coord in blocked_coords:
            assert (float(coord[0]), float(coord[1])) not in path
        
        assert len(path) > 0
        assert path[-1] == (9.0, 5.0)

    def test_multiple_enemies_spawned_and_moving(self):
        """测试多个敌人同时生成并移动。"""
        self.wave_manager.start_wave("wave_01_001")
        
        for _ in range(10):
            self.wave_manager.tick(delta=1.0)
        
        assert self.entity_manager.get_entity_count() == 5
        
        for entity in self.entity_manager.get_all_entities():
            transform = entity.get_component(TransformComponent)
            movement = entity.get_component(MovementComponent)
            
            assert transform is not None
            assert movement is not None
            assert movement.speed == 1.5

    def test_wave_manager_registered_as_service(self):
        """测试将 WaveManager 注册为服务。"""
        register_service(WaveManager, self.wave_manager)
        
        from CoreLogic import get_service as get_svc
        retrieved = get_svc(WaveManager)
        
        assert retrieved is self.wave_manager


class TestSpawnTask:
    """SpawnTask 数据类测试"""

    def test_create_spawn_task(self):
        """测试创建 SpawnTask 实例。"""
        task = SpawnTask(
            enemy_id="enemy_basic_001",
            spawn_time=0.0,
            count=5,
            spawn_interval=1.5
        )
        
        assert task.enemy_id == "enemy_basic_001"
        assert task.spawn_time == 0.0
        assert task.count == 5
        assert task.spawn_interval == 1.5
        assert task.last_spawn_time == -1.0
