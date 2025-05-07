# 用户注册和角色日程安排接口文档

## 1. 用户注册接口

### 请求

- **URL**: `/api/register_user`
- **方法**: `POST`
- **Content-Type**: `application/json`

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| code | String | 是 | 邀请码 |
| name | String | 是 | 用户名 |
| password | String | 是 | 密码 |
| twitter_id | String | 否 | Twitter ID（若有） |
| screen_name | String | 否 | Twitter 用户名（若有） |
| access_token | String | 否 | Twitter 访问令牌（若有） |
| access_token_secret | String | 否 | Twitter 访问令牌密钥（若有） |

### 响应

成功：
```json
{
  "status": "success",
  "message": "用户注册成功",
  "user_id": 123
}
```

失败：
```json
{
  "status": "error",
  "message": "错误信息"
}
```

## 2. 角色日程安排接口

### 请求

- **URL**: `/api/character/{character_id}/schedule`
- **方法**: `GET`
- **参数**:
  - `page`: 页码，默认为1
  - `page_size`: 每页数量，默认为5，最大为20

### 响应

成功：
```json
{
  "character_id": 123,
  "name": "角色名称",
  "activities": [
    {
      "start_minute": 480,  // 对应08:00
      "duration": 60,       // 持续60分钟
      "end_minute": 540,    // 对应09:00
      "action": "吃早餐",    // 活动内容
      "location": "kitchen", // 活动地点
      "icon_path": "/icon/kitchen.png", // 地点图标路径
      "icon_file": "kitchen.png",       // 图标文件名
      "site": "原始的site字段值"          // 原始site字段
    },
    // ... 更多活动
  ],
  "pagination": {
    "page": 1,               // 当前页码
    "page_size": 5,          // 每页数量
    "total_pages": 5,        // 总页数
    "total_activities": 24,  // 总活动数
    "has_next": true,        // 是否有下一页
    "has_prev": false        // 是否有上一页
  }
}
```

失败：
```json
{
  "status": "error",
  "message": "未找到该角色的日程安排"
}
```

## 注意事项

1. 图标文件位于`/icon/`目录，图标文件名为"地点.png"
2. 角色日程安排接口支持分页，避免一次性请求过多数据
3. 在使用图标时，建议添加错误处理：`onerror="this.src='/icon/default.png'"`

## 日程安排前端示例代码

```javascript
// 获取角色日程
async function fetchCharacterSchedule(characterId, page = 1, pageSize = 5) {
  try {
    const response = await fetch(`/api/character/${characterId}/schedule?page=${page}&page_size=${pageSize}`);
    if (!response.ok) {
      throw new Error('获取角色日程安排失败');
    }
    return await response.json();
  } catch (error) {
    console.error('获取日程失败:', error);
    throw error;
  }
}

// 滚动加载实现
let currentPage = 1;
let isLoading = false;
let hasMoreData = true;

async function loadMoreSchedules(characterId) {
  if (isLoading || !hasMoreData) return;
  
  isLoading = true;
  document.getElementById('loading').style.display = 'block';
  
  try {
    const data = await fetchCharacterSchedule(characterId, currentPage);
    
    // 渲染活动
    const container = document.getElementById('activities-container');
    data.activities.forEach(activity => {
      // 格式化时间
      const startHour = Math.floor(activity.start_minute / 60);
      const startMin = activity.start_minute % 60;
      const endHour = Math.floor(activity.end_minute / 60);
      const endMin = activity.end_minute % 60;
      
      const timeStr = `${startHour.toString().padStart(2, '0')}:${startMin.toString().padStart(2, '0')} - 
                       ${endHour.toString().padStart(2, '0')}:${endMin.toString().padStart(2, '0')}`;
      
      // 创建活动卡片
      const card = document.createElement('div');
      card.className = 'activity-card';
      card.innerHTML = `
        <div class="activity-time">${timeStr}</div>
        <div class="activity-title">${activity.action}</div>
        <div class="activity-location">
          <img src="${activity.icon_path}" alt="${activity.location}" onerror="this.src='/icon/default.png'">
          <span>${activity.location}</span>
        </div>
      `;
      
      container.appendChild(card);
    });
    
    // 更新分页状态
    currentPage++;
    hasMoreData = data.pagination.has_next;
    
    if (!hasMoreData) {
      document.getElementById('end-message').style.display = 'block';
    }
  } catch (error) {
    console.error(error);
  } finally {
    isLoading = false;
    document.getElementById('loading').style.display = hasMoreData ? 'block' : 'none';
  }
}

// 滚动事件监听
window.addEventListener('scroll', () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 200) {
    loadMoreSchedules(characterId);
  }
});

// 初始加载
loadMoreSchedules(characterId);
``` 