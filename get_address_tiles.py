from maza.maze import Maze

def main():
    # 初始化迷宫对象
    m = Maze("matrix2")
    
    # 将地址信息写入文件
    with open('address_list.txt', 'w', encoding='utf-8') as f:
        f.write("Address List:\n")
        f.write("-" * 50 + "\n")
        for address in sorted(m.address_tiles.keys()):
            f.write(f"{address}\n")

if __name__ == "__main__":
    main() 