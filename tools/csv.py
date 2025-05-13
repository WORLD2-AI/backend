from collections import deque

def find_continuous_regions(file_path):
    # Read the CSV file
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # 解析CSV内容为二维数组
    grid = []
    for line in lines:
        if line.strip():
            grid.append([int(num) for num in line.strip().split(',')])
    
    rows = len(grid)
    if rows == 0:
        return []
    cols = len(grid[0])
    visited = [[False for _ in range(cols)] for _ in range(rows)]
    result = []
    
    # 四连通方向：上下左右
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for i in range(rows):
        for j in range(cols):
            if not visited[i][j] and grid[i][j] != -1:
                val = grid[i][j]
                queue = deque()
                queue.append((i, j))
                visited[i][j] = True
                current_group = [(i, j)]
                
                while queue:
                    x, y = queue.popleft()
                    for dx, dy in directions:
                        nx = x + dx
                        ny = y + dy
                        if 0 <= nx < rows and 0 <= ny < cols:
                            if not visited[nx][ny] and grid[nx][ny] == val:
                                visited[nx][ny] = True
                                queue.append((nx, ny))
                                current_group.append((nx, ny))
                
                # 将当前区域的信息添加到结果中
                result.append({
                    'value': val,
                    'positions': current_group
                })
    
    return result

# 示例用法
file_path = "C:\\Users\\32742\\ai-hello-world\\map\\matrix2\\maze\\arena_maze.csv"
"""
[此处粘贴arena_maze.csv的内容]
"""
regions = find_continuous_regions(file_path)
for region in regions:
    print(f"Value: {region['value']}, Positions: {region['positions']}")