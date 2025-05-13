from celery_tasks.location_service import get_location_by_coordinates
import json
from base import root_path

def test_all_coordinates():
    """
    测试所有坐标点的位置信息
    返回一个字典，key为坐标(x,y)，value为位置名称
    """
    # 从配置文件读取地图大小
    with open(f"{root_path}/map/matrix2/maze_meta_info.json", 'r') as f:
        meta_info = json.load(f)
        maze_width = meta_info["maze_width"]
        maze_height = meta_info["maze_height"]
    
    # 存储结果的字典
    location_map = {}
    
    # 遍历所有坐标
    for x in range(maze_width):
        for y in range(maze_height):
            # 获取位置信息
            location = get_location_by_coordinates(x, y)
            if location:
                location_map[f"({x},{y})"] = location['full_path']
            else:
                location_map[f"({x},{y})"] = None
    
    return location_map

def save_results(location_map):
    """
    将结果保存到文件
    """
    # 保存完整结果
    with open('location_map_full.json', 'w', encoding='utf-8') as f:
        json.dump(location_map, f, ensure_ascii=False, indent=2)
    
    # 只保存有位置信息的坐标
    valid_locations = {k: v for k, v in location_map.items() if v is not None}
    with open('location_map_valid.json', 'w', encoding='utf-8') as f:
        json.dump(valid_locations, f, ensure_ascii=False, indent=2)

def print_statistics(location_map):
    """
    打印统计信息
    """
    total_coordinates = len(location_map)
    valid_locations = sum(1 for v in location_map.values() if v is not None)
    
    print(f"\n位置信息统计:")
    print(f"总坐标数: {total_coordinates}")
    print(f"有效位置数: {valid_locations}")
    print(f"空位置数: {total_coordinates - valid_locations}")
    print(f"位置覆盖率: {(valid_locations/total_coordinates)*100:.2f}%")

if __name__ == "__main__":
    print("开始测试所有坐标点的位置信息...")
    location_map = test_all_coordinates()
    
    print("保存结果到文件...")
    save_results(location_map)
    
    print_statistics(location_map)
    
    print("\n测试完成！")
    print("结果已保存到 location_map_full.json 和 location_map_valid.json")