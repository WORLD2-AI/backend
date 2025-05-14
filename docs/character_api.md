# 角色注册与位置检查接口文档

## 目录
1. [角色注册接口](#1-角色注册接口)
2. [位置检查接口](#2-位置检查接口)
3. [注意事项](#注意事项)

## 1. 角色注册接口

### 基本信息
- **接口URL**: `/api/register_role`
- **请求方式**: POST
- **Content-Type**: application/json
- **权限要求**: 需要登录（@login_required）

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
| x | number | 否 | 地图X坐标 |
| y | number | 否 | 地图Y坐标 |

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
    "x": 36,
    "y": 12
}
```

### 响应参数
| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态：'success' 或 'error' |
| message | string | 响应消息 |
| character_id | number | 注册成功时返回的角色ID |

### 响应示例
#### 成功响应
```json
{
    "status": "success",
    "message": "角色注册成功",
    "character_id": 123
}
```

#### 错误响应
```json
{
    "status": "error",
    "message": "该位置已被其他角色注册"
}
```

## 2. 位置检查接口

### 基本信息
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
| location_name | string | 位置名称 |
| room_name | string | 房间名称 |
| position_name | string | 位置名称 |
| is_room_registered | boolean | 房间是否已被注册 |
| is_location_registered | boolean | 位置是否已被注册 |
| my_room_info | object | 当前用户在该房间的角色信息 |
| current_person_name | string | 当前位置的人物名称 |
| current_position_name | string | 当前位置的名称 |

### 响应示例
#### 位置可用
```json
{
    "status": "success",
    "is_registered": false,
    "message": "位置可用",
    "location_name": "图书馆",
    "room_name": "阅读区",
    "position_name": "图书馆:阅读区",
    "is_room_registered": false,
    "is_location_registered": false,
    "my_room_info": {
        "has_character": false,
        "character_name": null,
        "character_id": null
    },
    "current_person_name": "",
    "current_position_name": "图书馆:阅读区"
}
```

#### 位置已被占用
```json
{
    "status": "success",
    "is_registered": true,
    "message": "该位置已被其他角色占用",
    "location_name": "图书馆",
    "room_name": "阅读区",
    "position_name": "图书馆:阅读区",
    "is_room_registered": true,
    "is_location_registered": false,
    "my_room_info": {
        "has_character": false,
        "character_name": null,
        "character_id": null
    },
    "current_person_name": "",
    "current_position_name": "图书馆:阅读区"
}
```

#### 参数错误
```json
{
    "status": "error",
    "message": "请提供x和y坐标"
}
```

## 注意事项

### 角色注册接口
1. 所有必填字段都不能为空
2. 年龄必须在1-120之间
3. 性别只能是'male'、'female'或'other'
4. 如果指定了位置（x和y坐标），系统会先检查该位置是否已被其他角色占用
5. 位置检查只考虑非系统角色（user_id不为0）的位置占用情况
6. 注册成功后，角色状态会被设置为"待审核"（PENDING）

### 位置检查接口
1. 坐标值必须是有效的整数
2. 位置检查只关注一级和二级位置，更细粒度的位置信息不会被检查或存储
3. 系统会同时检查位置和房间的占用情况
4. 返回的位置信息包含完整的层级结构（如：城市:区域:建筑:房间）

### 错误码说明
- 400: 请求参数错误（如缺少必填字段、参数格式不正确等）
- 401: 未登录（仅角色注册接口）
- 500: 服务器内部错误