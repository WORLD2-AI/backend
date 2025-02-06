from PIL import Image, ImageDraw
import random

# 参数设置
block_size = 32  # 每个色块的大小
gap = 1          # 分割线宽度
cols = 10        # 每行块数
rows = 25        # 总行数
total_blocks = 250  # 总块数

# 计算画布尺寸
width = cols * block_size + (cols - 1) * gap
height = rows * block_size + (rows - 1) * gap

# 创建新图像（黑色背景代表分割线）
img = Image.new('RGB', (width, height), color='black')
draw = ImageDraw.Draw(img)

# 生成250个不重复的随机颜色
colors = set()
while len(colors) < total_blocks:
    colors.add((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
colors = list(colors)

# 绘制色块
for index in range(total_blocks):
    row = index // cols
    col = index % cols
    
    # 计算块的位置
    x0 = col * (block_size + gap)
    y0 = row * (block_size + gap)
    x1 = x0 + block_size
    y1 = y0 + block_size
    
    # 绘制矩形
    draw.rectangle([x0, y0, x1, y1], fill=colors[index])

# 保存图片
img.save('pixel_map.png')
img.show()