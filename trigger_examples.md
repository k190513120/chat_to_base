# GitHub Actions 触发方式详解

## 方式一：使用 curl 命令

### 基本触发命令

```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/k190513120/chat_to_base/actions/workflows/sync-feishu-members.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "bitable_url": "https://bytedance.feishu.cn/base/你的base_id?table=你的table_id",
      "chat_id": "oc_你的群聊ID"
    }
  }'
```

### 实际使用示例

```bash
# 替换为你的实际参数
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/k190513120/chat_to_base/actions/workflows/sync-feishu-members.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "bitable_url": "https://bytedance.feishu.cn/base/YOUR_BASE_ID?table=YOUR_TABLE_ID",
      "chat_id": "oc_YOUR_CHAT_ID"
    }
  }'
```

## 方式二：使用 Python 脚本

### 直接运行脚本

```bash
# 触发工作流
python trigger_github_action.py "https://bytedance.feishu.cn/base/你的base_id?table=你的table_id" "oc_你的群聊ID"

# 查看运行状态
python trigger_github_action.py --status
```

### 脚本参数说明

- `bitable_url`: 飞书多维表格的完整URL
- `chat_id`: 飞书群聊ID（以 `oc_` 开头）

## 方式三：通过 GitHub 网页界面

1. 访问 https://github.com/k190513120/chat_to_base/actions
2. 点击 "Sync Feishu Group Members" 工作流
3. 点击 "Run workflow" 按钮
4. 填入必要参数：
   - `bitable_url`: 飞书多维表格URL
   - `chat_id`: 飞书群聊ID

## API 详细说明

### 请求头

```
Authorization: token YOUR_GITHUB_TOKEN
Accept: application/vnd.github.v3+json
Content-Type: application/json
```

### 请求体

```json
{
  "ref": "main",
  "inputs": {
    "bitable_url": "https://bytedance.feishu.cn/base/你的base_id?table=你的table_id",
    "chat_id": "oc_你的群聊ID"
  }
}
```

### 响应

成功时返回 HTTP 204 No Content

## 获取 GitHub Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择适当的权限：
   - `repo` (完整仓库访问权限)
   - `workflow` (工作流权限)
4. 复制生成的 token

## 获取飞书参数

### 获取多维表格 URL

1. 打开飞书多维表格
2. 复制浏览器地址栏中的完整URL
3. URL格式：`https://bytedance.feishu.cn/base/base_id?table=table_id`

### 获取群聊 ID

使用项目中的 `get_chat_id.py` 脚本：

```bash
python get_chat_id.py
```

## 工作流状态查看

### 方法一：GitHub 网页
访问 https://github.com/k190513120/chat_to_base/actions 查看工作流执行状态

### 方法二：使用 API 查询
```bash
curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/repos/k190513120/chat_to_base/actions/workflows/sync-feishu-members.yml/runs
```

### 方法三：使用 Python 脚本
```bash
python trigger_github_action.py --status
```

## 注意事项

1. **GitHub Token 安全**：
   - 不要在代码中硬编码 token
   - 使用环境变量或安全的配置文件
   - 定期更新 token

2. **飞书权限**：
   - 确保机器人有群聊管理权限
   - 确保机器人有多维表格访问权限

3. **工作流限制**：
   - GitHub Actions 有使用限制
   - 避免频繁触发工作流

4. **错误处理**：
   - 检查工作流日志了解错误原因
   - 验证输入参数的正确性