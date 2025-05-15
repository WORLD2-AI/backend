import csv
from collections import deque

def read_csv_matrix(path):
    with open(path, newline='', encoding='utf-8') as f:
        return [row for row in csv.reader(f)]

def write_csv_matrix(path, matrix):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(matrix)

def flood_fill(matrix, x, y, target, new_value):
    h, w = len(matrix), len(matrix[0])
    if matrix[y][x] != target:
        return
    q = deque()
    q.append((x, y))
    visited = set()
    while q:
        cx, cy = q.popleft()
        if (cx, cy) in visited:
            continue
        visited.add((cx, cy))
        if 0 <= cx < w and 0 <= cy < h and matrix[cy][cx] == target:
            matrix[cy][cx] = new_value
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = cx+dx, cy+dy
                if 0 <= nx < w and 0 <= ny < h and matrix[ny][nx] == target:
                    q.append((nx, ny))

def replace_area(csv_path, x, y, new_value):
    matrix = read_csv_matrix(csv_path)
    target = matrix[y][x]
    flood_fill(matrix, x, y, target, str(new_value))
    write_csv_matrix(csv_path, matrix)
    return matrix

# 用法示例：
# replace_area('map/matrix2/maze/arena_maze.csv', x, y, arena_id)
# replace_area('map/matrix2/maze/sector_maze.csv', x, y, sector_id)
