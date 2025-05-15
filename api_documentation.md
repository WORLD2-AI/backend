# AI-Hello-World项目接口文档

## 基础信息
- 服务器地址: http://127.0.0.1:5000
- API前缀: /api

## 一、角色相关接口

### 1. 获取角色详情
- **接口**: GET `/api/character/{character_id}/detail`
- **描述**: 获取指定角色的详细信息，包括当前活动、位置和图标路径
- **参数**: 
  - `character_id`: 角色ID
- **返回示例**:
```json
{
  "id": 1,
  "name": "角色名称",
  "activity": "正在进行的活动",
  "location": "当前位置",
  "icon_path": "/icon/位置名称.png",
  "icon_file": "位置名称.png",
  "icon_dir": "icon",
  "start_minute": 540,
  "duration": 60,
  "current_time_minutes": 550
}
```

### 2. 获取角色状态
- **接口**: GET `/api/character/{character_id}/status`
- **描述**: 获取角色当前状态
- **参数**: 
  - `character_id`: 角色ID
- **返回示例**:
```json
{
  "status": "success",
  "character_status": "online",
  "character_id": 1
}
```

### 3. 获取角色列表
- **接口**: GET `/api/characters`
- **描述**: 获取当前登录用户的所有角色
- **权限**: 需要登录
- **返回示例**:
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "角色1",
      "current_location": "图书馆",
      "current_action": "读书"
    },
    {
      "id": 2,
      "name": "角色2",
      "current_location": "公园",
      "current_action": "散步"
    }
  ]
}
```

### 4. 获取角色详细信息
- **接口**: GET `/api/characters/{character_id}`
- **描述**: 获取特定角色的详细信息，包括日程安排
- **参数**: 
  - `character_id`: 角色ID
- **返回示例**:
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "name": "角色名称",
    "current_location": "图书馆",
    "current_action": "读书",
    "schedules": [
      {
        "id": 1,
        "start_minute": 540,
        "duration": 60,
        "action": "读书",
        "site": "位置:图书馆:阅读区"
      }
    ]
  }
}
```

### 5. 删除角色
- **接口**: DELETE `/api/character/{character_id}`
- **描述**: 删除指定角色及其相关数据
- **参数**: 
  - `character_id`: 角色ID
- **返回示例**:
```json
{
  "status": "success",
  "message": "角色删除成功",
  "character_id": 1
}
```

## 二、用户相关接口

### 1. 用户注册
- **接口**: POST `/api/register_user`
- **描述**: 注册新用户
- **请求参数**:
  - `username`: 用户名
  - `password`: 密码
  - `invitation_code`: 邀请码
- **返回示例**:
  - 成功时重定向到注册成功页面
  - 失败时返回带有错误信息的注册页面
```html
<!DOCTYPE html>
<html>
  <!-- 注册成功页面HTML -->
  <h1 class="h3 mb-3">注册成功</h1>
  <p class="lead">欢迎，用户名！您的账号已成功创建。</p>
</html>
```

### 2. 用户登录
- **接口**: POST `/api/login`
- **描述**: 用户登录
- **请求参数**:
  - `username`: 用户名
  - `password`: 密码
- **返回示例**:
  - 成功时重定向到首页
  - 失败时返回带有错误信息的登录页面
```html
<!-- 登录失败时 -->
<div class="alert alert-danger" role="alert">
  用户名或密码错误
</div>
```

### 3. 获取用户信息
- **接口**: GET `/user/info`
- **描述**: 获取当前登录用户信息
- **权限**: 需要登录
- **返回示例**:
```json
{
  "data": {
    "id": 1,
    "username": "用户名",
    "twitter_id": "推特ID",
    "screen_name": "屏幕名称"
  }
}
```
- **未登录时返回**:
```json
{
  "data": null
}
```

### 4. 获取用户资料
- **接口**: GET `/api/user/profile`
- **描述**: 获取用户完整资料
- **权限**: 需要登录
- **返回示例**:
```json
{
  "status": "success",
  "id": 1,
  "username": "用户名",
  "twitter_id": "推特ID"
}
```

### 5. 用户登出
- **接口**: POST `/logout`
- **描述**: 安全退出登录
- **权限**: 需要登录
- **返回示例**:
```json
{
  "status": "success",
  "message": "logout success!"
}
```

## 三、角色可见性相关接口

### 1. 获取可见角色
- **接口**: GET `/api/visible-characters/{character_id}`
- **描述**: 获取指定角色周围可见的其他角色
- **参数**: 
  - `character_id`: 角色ID
- **返回示例**:
```json
{
  "status": "success",
  "data": [
    {
      "character_id": "char2",
      "position": [40, 40],
      "distance": 14.14,
      "name": "kiki",
      "avatar": "/static/avatars/mage.png",
      "status": "online",
      "level": 8,
      "class": "Unknown"
    }
  ]
}
```

### 2. 获取可见角色（带半径参数）
- **接口**: GET `/api/visible-characters-in-radius/{character_id}`
- **描述**: 获取指定半径内的可见角色
- **参数**: 
  - `character_id`: 角色ID
  - `radius`: 查询半径（可选）
- **返回示例**:
```json
{
  "status": "success",
  "data": {
    "visible_characters": [
      {
        "id": "char2",
        "name": "kiki",
        "position": [40, 40],
        "distance": 14.14,
        "status": "online" 
      }
    ],
    "radius": 20,
    "total_visible": 1
  }
}
```

### 3. 更新角色位置
- **接口**: POST `/api/update-character-position/{character_id}`
- **描述**: 更新角色的位置信息
- **参数**: 
  - `character_id`: 角色ID
  - 请求体: `{"position": [x, y]}`
- **返回示例**:
```json
{
  "status": "success",
  "data": {
    "character_id": "char1",
    "position": [55, 48],
    "name": "frank",
    "status": "online"
  },
  "message": "位置更新成功"
}
```

## 四、Twitter 登录相关接口

### 1. Twitter 登录
- **接口**: GET `/login/twitter`
- **描述**: 通过 Twitter 进行第三方登录
- **参数**: 
  - `callback`: 回调URL
- **返回**: 重定向到 Twitter 授权页面

### 2. Twitter 登录回调
- **接口**: GET `/callback`
- **描述**: Twitter 授权回调处理
- **参数**: 
  - `oauth_verifier`: OAuth 验证码
  - `action`: 操作类型（可选，bind 表示绑定账号）
- **返回示例**:
  - 登录成功后重定向到回调URL
  - 绑定成功时:
```html
Twitter 账户绑定成功！
```
  - 用户未注册时重定向到注册页面

### 3. 绑定 Twitter 账号
- **接口**: GET `/bind_twitter`
- **描述**: 为当前用户绑定 Twitter 账号
- **权限**: 需要登录
- **返回**: 重定向到 Twitter 授权页面

## 五、页面路由

### 1. 角色详情页
- **接口**: GET `/character/{character_id}`
- **描述**: 渲染角色详情页面
- **参数**: 
  - `character_id`: 角色ID
- **返回**: 角色详情页HTML
```html
<!DOCTYPE html>
<html>
  <!-- 角色详情页HTML内容 -->
  <h1>角色详情</h1>
  <div id="character-container">
    <!-- 角色信息将通过JavaScript加载 -->
  </div>
</html>
```

### 2. 用户注册页
- **接口**: GET `/register`
- **描述**: 重定向到用户注册页
- **返回**: 重定向到 `/api/register_user`

### 3. 角色注册页
- **接口**: GET `/register_role`
- **描述**: 重定向到角色注册页
- **返回**: 重定向到 `/api/register_role`
```html
<!DOCTYPE html>
<html>
  <!-- 角色注册页HTML内容 -->
  <h1>角色注册</h1>
  <form method="post" action="/api/register_character">
    <!-- 表单内容 -->
  </form>
</html>
```

### 4. 角色列表页
- **接口**: GET `/character_list`
- **描述**: 重定向到角色列表页
- **返回**: 重定向到 `/characters`
```html
<!DOCTYPE html>
<html>
  <!-- 角色列表页HTML内容 -->
  <h1>角色列表</h1>
  <div id="character-list">
    <!-- 角色列表将通过JavaScript加载 -->
  </div>
</html>
```

### 4. 获取所有角色（含系统角色）
- **接口**: GET `/api/all-chars`
- **描述**: 获取系统角色和所有在线用户角色
- **返回示例**:
```json
{
  "status": "success",
  "data": {
    "characters": [
      {
        "id": 0,
        "name": "系统角色",
        "user_id": 0,
        "status": "online"
      },
      {
        "id": 123,
        "name": "用户角色",
        "user_id": 1,
        "status": "online"
      }
    ],
    "system_character_count": 1,
    "online_user_character_count": 1
  }
}
```
- **返回**: 角色详情页HTML
```html
<!DOCTYPE html>
<html>
  <!-- 角色详情页HTML内容 -->
  <h1>角色详情</h1>
  <div id="character-container">
    <!-- 角色信息将通过JavaScript加载 -->
  </div>
</html>
```

## 注意事项

1. 大部分API接口需要用户登录状态
2. 图标路径格式为 `/icon/{location}.png`，确保服务器上存在对应图片
3. 角色日程中的地点信息格式应为 `xxx:位置:xxx`
4. 服务器运行在 5000 端口，跨域已配置