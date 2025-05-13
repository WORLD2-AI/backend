# 角色位置相关接口文档

## 目录
1. [检查位置是否可用](#1-检查位置是否可用)
2. [注册角色（带位置信息）](#2-注册角色带位置信息)
3. [注意事项](#注意事项)
4. [测试页面](#测试页面)

## 1. 检查位置是否可用

### 接口说明
检查指定坐标位置是否已被非系统角色占用。

### 请求信息
- **接口URL**: `/api/check_location`
- **请求方式**: GET
- **Content-Type**: application/json

### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| x | number | 是 | 地图X坐标 |
| y | number | 是 | 地图Y坐标 |

### 请求示例
```
GET /api/check_location?x=36&y=12
```

### 响应参数
| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态：'success' 或 'error' |
| is_registered | boolean | 位置是否已被占用 |
| message | string | 响应消息 |

### 响应示例
```json
// 位置可用
{
    "status": "success",
    "is_registered": false,
    "message": "位置可用"
}

// 位置已被占用
{
    "status": "success",
    "is_registered": true,
    "message": "位置已被其他角色注册"
}

// 参数错误
{
    "status": "error",
    "message": "请提供x和y坐标"
}
```

## 2. 注册角色（带位置信息）

### 接口说明
注册新角色，可选择性地指定角色家的位置。

### 请求信息
- **接口URL**: `/api/register_role`
- **请求方式**: POST
- **Content-Type**: application/json

### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 是 | 角色名 |
| first_name | string | 是 | 名 |
| last_name | string | 是 | 姓 |
| age | number | 是 | 年龄（1-120） |
| sex | string | 是 | 性别（'male'/'female'/'other'） |
| innate | string | 是 | 天赋 |
| learned | string | 是 | 学习 |
| currently | string | 是 | 当前状态 |
| lifestyle | string | 是 | 生活方式 |
| house | string | 否 | 家的位置，格式为"x,y"（例如："36,12"） |

### 请求示例
```json
{
    "name": "张三",
    "first_name": "三",
    "last_name": "张",
    "age": 25,
    "sex": "male",
    "innate": "聪明",
    "learned": "编程",
    "currently": "学习",
    "lifestyle": "积极",
    "house": "36,12"
}
```

### 响应参数
| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态：'success' 或 'error' |
| message | string | 响应消息 |
| character_id | number | 注册成功时返回的角色ID |

### 响应示例
```json
// 注册成功
{
    "status": "success",
    "message": "角色注册成功",
    "character_id": 123
}

// 位置已被占用
{
    "status": "error",
    "message": "该位置已被其他角色注册"
}

// 参数错误
{
    "status": "error",
    "message": "缺少必填字段: name"
}
```

### 错误码说明
| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |

## 注意事项

1. 位置检查只考虑非系统角色（user_id不为0）的位置占用情况
2. 坐标值必须是有效的整数
3. house字段格式必须为"x,y"，例如："36,12"
4. 注册角色时，如果指定了位置，会先检查该位置是否可用
5. 所有必填字段都不能为空
6. 年龄必须在1-120之间
7. 性别只能是'male'、'female'或'other'

## 测试页面

提供了一个测试页面用于测试这两个接口：
- 访问地址：`/location_test`
- 包含位置检查和角色注册两个功能模块
- 提供直观的表单界面和结果展示

### 测试页面功能
1. 位置检查
   - 输入X和Y坐标
   - 显示位置是否可用
   - 实时显示检查结果

2. 角色注册
   - 填写完整的角色信息
   - 可选填写位置信息
   - 显示注册结果
   - 注册成功后自动清空表单

### 使用建议
1. 建议先使用位置检查功能确认位置可用
2. 确认位置可用后再进行角色注册
3. 注册时注意填写所有必填字段
4. 注意年龄和性别的限制条件 