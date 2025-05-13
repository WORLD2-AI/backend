import csv
import mysql.connector
from mysql.connector import Error

def process_line(line):
    # 分割行内容
    parts = line.strip().split(',')
    if len(parts) >= 3:
        # 获取第二个逗号后的内容
        content = ','.join(parts[2:])
        # 将第三个逗号替换为冒号
        if ',' in content:
            content = content.replace(',', ':', 1)
        return content
    return None

def import_arena_blocks():
    try:
        # 连接MySQL数据库
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  # 请替换为你的MySQL用户名
            password='123456',  # 请替换为你的MySQL密码
            database='character_db'
        )

        if connection.is_connected():
            cursor = connection.cursor()
            
            # 获取当前最大id
            cursor.execute("SELECT MAX(id) FROM arena_blocks")
            result = cursor.fetchone()
            current_id = result[0] if result[0] is not None else 0
            
            # 读取CSV文件
            csv_file_path = r'C:\Users\32742\ai-hello-world\map\matrix2\special_blocks\arena_blocks.csv'
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if row:  # 确保行不为空
                        # 处理行数据
                        processed_content = process_line(','.join(row))
                        if processed_content:
                            # 插入数据到数据库
                            current_id += 1
                            insert_query = "INSERT INTO arena_blocks (id, arena_block) VALUES (%s, %s)"
                            cursor.execute(insert_query, (current_id, processed_content))
            
            # 提交事务
            connection.commit()
            print(f"数据导入成功！共导入 {current_id} 条记录")

    except Error as e:
        print(f"发生错误: {e}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("数据库连接已关闭")

if __name__ == "__main__":
    import_arena_blocks() 