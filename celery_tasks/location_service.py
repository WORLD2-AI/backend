from base import *
import json
import os
from maza.maze_db import Maze

def check_if_file_exists(file_path: str) -> bool:
    """
    检查文件是否存在
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        bool: 文件是否存在
    """
    return os.path.exists(file_path)

class MemoryTree:
    def __init__(self, f_saved):
        self.tree = {}
        if check_if_file_exists(f_saved):
            self.tree = json.load(open(f_saved))
            
    def get_str_accessible_sectors(self, curr_world):
        x = ", ".join(list(self.tree[curr_world].keys()))
        return x

    def get_str_accessible_sector_arenas(self, sector):
        curr_world, curr_sector = sector.split(":")
        if not curr_sector:
            return ""
        x = ", ".join(list(self.tree[curr_world][curr_sector].keys()))
        return x
        
    def get_str_accessible_arena_game_objects(self, arena):
        curr_world, curr_sector, curr_arena = arena.split(":")

        if not curr_arena: 
            return ""
        x = None
        try: 
            data = self.tree[curr_world][curr_sector].get(curr_arena,"")
            if data is None:
                data = self.tree[curr_world][curr_sector].get(curr_arena.lower(),"")
            if data is not None:
                x = ", ".join(list(data))
        except: 
            x = None
        return x
        
    def get_all_str_accessible_positions(self, curr_world):
        sectors = self.get_str_accessible_sectors(curr_world)
        all_areas = []
        result_position_list = []
        for sector in sectors.split(", "):
            if sector != "":
                tmp_arr = self.get_str_accessible_sector_arenas(f"{curr_world}:{sector}").split(", ")
                for arena in tmp_arr:
                    if arena != "":
                        all_areas += [f"{curr_world}:{sector}:{arena}"]
        for i in all_areas:
            if i:
                object_list_str = self.get_str_accessible_arena_game_objects(i) 
                if object_list_str != "":
                    object_list = object_list_str.split(", ")
                    for j in object_list:
                        result_position_list += [f"{i}:{j}"]
        return result_position_list

def get_location_by_name(location_name: str) -> dict:
    """
    根据地点名称返回对应的位置信息
    
    Args:
        location_name (str): 地点名称，例如 "common room", "kitchen" 等
        
    Returns:
        dict: 包含位置信息的字典，格式如下：
        {
            "world": "the ville",
            "sector": "artist's co-living space",
            "arena": "common room",
            "object": "sofa",
            "full_path": "the ville:artist's co-living space:common room:sofa"
        }
        如果未找到位置，返回 None
    """
    memory_tree = MemoryTree(f'{root_path}/map/matrix2/base.json')
    world = "the ville"  # 默认世界
    
    # 获取所有可访问的位置
    all_positions = memory_tree.get_all_str_accessible_positions(world)
    
    # 遍历所有位置查找匹配的地点
    for position in all_positions:
        if position.lower().find(location_name.lower()) != -1:
            # 解析位置路径
            parts = position.split(":")
            if len(parts) >= 4:
                return {
                    "world": parts[0],
                    "sector": parts[1],
                    "arena": parts[2],
                    "object": parts[3],
                    "full_path": position
                }
    
    return None

def get_all_locations() -> list:
    """
    获取所有可用的位置信息
    
    Returns:
        list: 包含所有位置信息的列表，每个位置是一个字典
    """
    memory_tree = MemoryTree(f'{root_path}/map/matrix2/base.json')
    world = "the ville"
    all_positions = memory_tree.get_all_str_accessible_positions(world)
    
    locations = []
    for position in all_positions:
        parts = position.split(":")
        if len(parts) >= 4:
            locations.append({
                "world": parts[0],
                "sector": parts[1],
                "arena": parts[2],
                "object": parts[3],
                "full_path": position
            })
    
    return locations

def get_location_coordinates(location_name: str) -> tuple:
    """
    根据地点名称返回对应的坐标信息
    
    Args:
        location_name (str): 地点名称，例如 "common room", "kitchen" 等
        
    Returns:
        tuple: 包含坐标信息的元组 (x, y)，如果未找到返回 None
    """
    memory_tree = MemoryTree(f'{root_path}/map/matrix2/base.json')
    world = "the ville"  # 默认世界
    maze = Maze(world)
    
    # 获取所有可访问的位置
    all_positions = memory_tree.get_all_str_accessible_positions(world)
    
    # 遍历所有位置查找匹配的地点
    for position in all_positions:
        if position.lower().find(location_name.lower()) != -1:
            # 解析位置路径
            parts = position.split(":")
            if len(parts) >= 4:
                # 获取该位置的坐标
                for x in range(maze.maze_width):
                    for y in range(maze.maze_height):
                        tile = maze.access_tile((x, y))
                        if tile and tile.get("world") == parts[0] and tile.get("sector") == parts[1] and tile.get("arena") == parts[2]:
                            return (x, y)
    
    return None
maze = Maze("the ville")
def get_location_by_coordinates(x: int, y: int) -> dict:
    """
    根据坐标返回对应的位置信息，只返回三级位置
    
    Args:
        x (int): X坐标
        y (int): Y坐标
        
    Returns:
        dict: 包含位置信息的字典，格式如下：
        {
            "world": "the ville",
            "sector": "artist's co-living space",
            "arena": "common room",
            "full_path": "the ville:artist's co-living space:common room"
        }
        如果坐标无效或未找到位置，返回 None
    """
    try:
        tile = maze.access_tile((x, y))
        
        if not tile:
            return None
            
        # 获取三级位置
        world = tile.get("world", "")
        sector = tile.get("sector", "")
        arena = tile.get("arena", "")
        
        if not world or not sector or not arena:
            return None
            
        # 构建包含三级的完整路径
        full_path = f"{world}:{sector}:{arena}"
        
        return {
            "world": world,
            "sector": sector,
            "arena": arena,
            "full_path": full_path
        }
        
    except Exception as e:
        logger.error(f"获取位置信息失败: {str(e)}")
        return None

def get_all_positions_by_name(location_name: str) -> list:
    """
    根据地点名称返回该地点占用的所有位置信息
    
    Args:
        location_name (str): 地点名称，例如 "common room", "kitchen" 等
        
    Returns:
        list: 包含所有匹配位置信息的列表，每个位置是一个字典，格式如下：
        [{
            "world": "the ville",
            "sector": "artist's co-living space",
            "arena": "common room",
            "object": "sofa",
            "full_path": "the ville:artist's co-living space:common room:sofa",
            "coordinates": (x, y)
        }]
        如果未找到位置，返回空列表
    """
    memory_tree = MemoryTree(f'{root_path}/map/matrix2/base.json')
    world = "the ville"  # 默认世界
    maze = Maze(world)
    
    # 获取所有可访问的位置
    all_positions = memory_tree.get_all_str_accessible_positions(world)
    matching_positions = []
    
    # 遍历所有位置查找匹配的地点
    for position in all_positions:
        if position.lower().find(location_name.lower()) != -1:
            # 解析位置路径
            parts = position.split(":")
            if len(parts) >= 4:
                # 获取该位置的坐标
                for x in range(maze.maze_width):
                    for y in range(maze.maze_height):
                        tile = maze.access_tile((x, y))
                        if tile and tile.get("world") == parts[0] and tile.get("sector") == parts[1] and tile.get("arena") == parts[2]:
                            matching_positions.append({
                                "world": parts[0],
                                "sector": parts[1],
                                "arena": parts[2],
                                "object": parts[3],
                                "full_path": position,
                                "coordinates": (x, y)
                            })
    
    return matching_positions

def get_all_coordinates_by_name(location_name: str) -> list:
    """
    根据地点名称返回该地点占用的所有坐标
    
    Args:
        location_name (str): 地点名称，例如 "common room", "kitchen" 等
        
    Returns:
        list: 包含所有匹配位置的坐标列表，格式如下：
        [87, 50, 87, 51, 88, 40, 88, 41, 88, 42]
        如果未找到位置，返回空列表
    """
    try:
        memory_tree = MemoryTree(f'{root_path}/map/matrix2/base.json')
        maze = Maze("the ville")
        coordinates_list = []
        
        # 遍历迷宫中的所有坐标
        for x in range(maze.maze_width):
            for y in range(maze.maze_height):
                tile = maze.access_tile((x, y))
                if tile and location_name.lower() in str(tile).lower():
                    coordinates_list.extend([x, y])
        
        return coordinates_list
        
    except Exception as e:
        logger.error(f"获取坐标失败: {str(e)}")
        return []

def get_coordinates_for_object(location_name: str) -> list:
    """
    根据地点名称返回该地点占用的所有坐标点
    
    Args:
        location_name (str): 地点名称，例如 "library sofa"
        
    Returns:
        list: 包含所有坐标点的列表，每个坐标点是一个元组 (x, y)
    """
    positions = get_all_positions_by_name(location_name)
    coordinates = []
    for pos in positions:
        coordinates.append(pos['coordinates'])
    return coordinates

if __name__ == "__main__":
    while True:
        print("\n位置查询服务")
        print("1. 根据地点名称查询坐标")
        print("2. 根据坐标查询地点")
        print("3. 查看所有位置")
        print("4. 查询地点占用的所有位置")
        print("5. 退出")
        choice = input("请选择功能 (1-5): ")
        
        if choice == "1":
            location_name = input("请输入要查询的地点名称: ")
            coordinates = get_location_coordinates(location_name)
            print("-" * 50)
            if coordinates:
                print(f"找到位置 '{location_name}' 的坐标:")
                print(f"X坐标: {coordinates[0]}")
                print(f"Y坐标: {coordinates[1]}")
            else:
                print(f"未找到位置 '{location_name}' 的坐标")
            print("-" * 50)
            
        elif choice == "2":
            try:
                x = int(input("请输入X坐标: "))
                y = int(input("请输入Y坐标: "))
                location = get_location_by_coordinates(x, y)
                print("-" * 50)
                if location:
                    print(f"坐标 ({x}, {y}) 对应的位置:")
                    print(f"世界: {location['world']}")
                    print(f"区域: {location['sector']}")
                    print(f"完整路径: {location['full_path']}")
                else:
                    print(f"未找到坐标 ({x}, {y}) 对应的位置")
                print("-" * 50)
            except ValueError:
                print("请输入有效的坐标数字")
                
        elif choice == "3":
            locations = get_all_locations()
            print("-" * 50)
            print("所有可用位置:")
            for location in locations:
                print(f"世界: {location['world']}")
                print(f"区域: {location['sector']}")
                print(f"场所: {location['arena']}")
                print(f"物体: {location['object']}")
                print(f"完整路径: {location['full_path']}")
                print("-" * 30)
                
        elif choice == "4":
            location_name = input("请输入要查询的地点名称: ")
            coordinates = get_coordinates_for_object(location_name)
            print("-" * 50)
            if coordinates:
                print(f"位置 '{location_name}' 的坐标数组:")
                print(coordinates)
            else:
                print(f"未找到位置 '{location_name}' 的坐标")
            print("-" * 50)
            
        elif choice == "5":
            print("感谢使用位置查询服务！")
            break
            
        else:
            print("无效的选择，请重新输入") 