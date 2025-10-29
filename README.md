# 飞书群成员同步工具

这是一个用于将飞书群成员信息同步到飞书多维表格的工具，支持多种调用方式。

## 功能特性

- 🚀 **多种调用方式**：支持命令行、HTTP API、GitHub Actions
- 📊 **智能字段映射**：自动识别多维表格中的人员、群名称、租户ID字段
- 🔄 **批量处理**：支持大量群成员的批量同步
- 🐳 **容器化部署**：提供Docker支持，便于部署
- 📝 **详细日志**：完整的操作日志记录
- ✅ 自动获取飞书群所有成员信息
- ✅ 支持大群成员分页获取
- ✅ 自动解析多维表格URL获取表格信息
- ✅ 智能识别人员字段类型
- ✅ 批量写入多维表格，支持大量数据处理
- ✅ 完整的错误处理和日志记录
- ✅ 可配置的请求间隔，避免API限流

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/k190513120/chat_to_base.git
cd chat_to_base

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置飞书应用

1. 在飞书开放平台创建应用
2. 获取 `App ID` 和 `App Secret`
3. 配置应用权限：
   - `im:chat:readonly` - 获取群信息
   - `im:chat.member:readonly` - 获取群成员
   - `bitable:app:readonly` - 读取多维表格
   - `bitable:app:readwrite` - 写入多维表格

## 使用方法

### 方法一：命令行调用

```bash
# 设置环境变量
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"

# 运行脚本
python feishu_group_members.py
```

### 方法二：HTTP API 调用

#### 启动API服务

```bash
# 本地启动
python api_server.py

# 或使用uvicorn
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

#### API接口说明

**基础信息**
- 服务地址：`http://localhost:8000`
- API文档：`http://localhost:8000/docs`

**主要接口**

1. **异步同步接口** `POST /sync`
   ```bash
   curl -X POST "http://localhost:8000/sync" \
        -H "Content-Type: application/json" \
        -d '{
          "bitable_url": "https://example.feishu.cn/base/your_base_id?table=your_table_id",
          "chat_id": "oc_your_chat_id"
        }'
   ```

2. **同步同步接口** `POST /sync/immediate`
   ```bash
   curl -X POST "http://localhost:8000/sync/immediate" \
        -H "Content-Type: application/json" \
        -d '{
          "bitable_url": "https://example.feishu.cn/base/your_base_id?table=your_table_id",
          "chat_id": "oc_your_chat_id"
        }'
   ```

3. **查询任务状态** `GET /task/{task_id}`
   ```bash
   curl "http://localhost:8000/task/sync_20241225_143000_1234"
   ```

4. **健康检查** `GET /health`
   ```bash
   curl "http://localhost:8000/health"
   ```

### 方法三：GitHub Actions 调用

#### 配置 GitHub Secrets

在仓库设置中添加以下 Secrets：

- `FEISHU_APP_ID`: 飞书应用ID
- `FEISHU_APP_SECRET`: 飞书应用密钥
- `DEFAULT_CHAT_ID`: 默认群聊ID（可选）
- `DEFAULT_BITABLE_URL`: 默认多维表格URL（可选）

#### 手动触发

1. 进入 GitHub 仓库的 Actions 页面
2. 选择 "Sync Feishu Group Members" 工作流
3. 点击 "Run workflow"
4. 输入参数：
   - `bitable_url`: 多维表格URL
   - `chat_id`: 群聊ID

#### 定时执行

工作流已配置为每天北京时间上午9点自动执行（使用默认参数）。

#### API调用触发

```bash
# 使用GitHub API触发工作流
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/k190513120/chat_to_base/actions/workflows/sync-feishu-members.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "bitable_url": "https://example.feishu.cn/base/your_base_id?table=your_table_id",
      "chat_id": "oc_your_chat_id"
    }
  }'
```

### 方法四：Docker 部署

#### 构建镜像

```bash
docker build -t feishu-sync .
```

#### 运行容器

```bash
docker run -d \
  --name feishu-sync-api \
  -p 8000:8000 \
  -e FEISHU_APP_ID="your_app_id" \
  -e FEISHU_APP_SECRET="your_app_secret" \
  feishu-sync
```

#### 使用 docker-compose

创建 `docker-compose.yml`：

```yaml
version: '3.8'
services:
  feishu-sync:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FEISHU_APP_ID=your_app_id
      - FEISHU_APP_SECRET=your_app_secret
      - PORT=8000
    restart: unless-stopped
```

运行：
```bash
docker-compose up -d
```

## 参数说明

### 必需参数

- `bitable_url`: 飞书多维表格URL
  - 格式：`https://example.feishu.cn/base/{app_token}?table={table_id}`
- `chat_id`: 飞书群聊ID
  - 格式：`oc_xxxxxxxxxx`

### 可选参数

- `app_id`: 飞书应用ID（优先使用环境变量）
- `app_secret`: 飞书应用密钥（优先使用环境变量）

## 字段映射规则

工具会自动识别多维表格中的字段：

1. **人员字段**：
   - 优先选择"人员"类型字段（type=11）
   - 备选：文本类型字段（type=1）

2. **群名称字段**：
   - 优先选择包含"群"或"名称"的文本字段
   - 备选：第二个文本字段

3. **租户ID字段**：
   - 优先选择包含"租户"或"tenant"的文本字段
   - 备选：第三个文本字段

## 权限配置

<mcreference link="https://feishu.apifox.cn/" index="3">3</mcreference> <mcreference link="https://feishu.apifox.cn/doc-444610" index="4">4</mcreference>

### 必需权限

脚本需要以下飞书API权限：

| 权限范围 | 权限名称 | 用途 |
|---------|---------|------|
| 即时消息 | `im:chat` | 获取群基本信息 |
| 即时消息 | `im:chat.member` | 获取群成员列表 |
| 通讯录 | `contact:user.base` | 获取用户详细信息 |
| 多维表格 | `bitable:app` | 操作多维表格 |
| 云文档 | `drive:drive` | 访问云文档空间 |

### 权限申请流程

1. 在飞书开放平台的应用管理页面申请相应权限
2. 创建应用版本并提交审核
3. 等待企业管理员审核通过

## 字段类型支持

脚本会自动识别多维表格中的字段类型：

- **人员字段（推荐）**：直接存储飞书用户ID，支持@功能
- **文本字段（备选）**：存储用户姓名和邮箱信息

## 配置参数说明

### API配置

```python
API_CONFIG = {
    # 飞书开放平台API基础URL
    "base_url": "https://open.feishu.cn/open-apis",
    
    # 请求间隔时间（秒）- 避免触发限流
    "request_interval": 0.1,
    
    # 批量处理大小 - 每次写入的记录数
    "batch_size": 500,
    
    # token提前刷新时间（秒）
    "token_refresh_advance": 300
}
```

### 日志配置

```python
LOG_CONFIG = {
    # 日志级别：DEBUG, INFO, WARNING, ERROR
    "level": "INFO",
    
    # 日志文件名
    "filename": "feishu_sync.log",
    
    # 日志格式
    "format": "%(asctime)s - %(levelname)s - %(message)s"
}
```

## 错误处理

脚本包含完整的错误处理机制：

- **网络错误**：自动重试机制
- **权限错误**：详细的权限配置指导
- **数据错误**：跳过无效数据，继续处理
- **限流处理**：自动调整请求频率

## 日志文件

脚本运行时会生成 `feishu_sync.log` 日志文件，记录：

- 操作进度信息
- 错误和警告信息
- API调用详情
- 数据处理统计

## 注意事项

1. **API限流**：飞书API有调用频率限制，脚本已内置请求间隔控制
2. **大群处理**：对于成员数量很多的群，处理时间会较长，请耐心等待
3. **权限要求**：确保应用有足够的权限访问群信息和多维表格
4. **数据安全**：请妥善保管应用密钥，不要泄露给他人

## 常见问题

### Q: 提示"没有云空间节点的权限"

A: 需要将多维表格分享给包含应用机器人的群组，具体步骤：
1. 在应用后台开启机器人能力
2. 创建群组并添加应用机器人
3. 将多维表格分享给该群组

### Q: 获取不到群成员信息

A: 检查以下几点：
1. 群ID是否正确
2. 应用是否有 `im:chat.member` 权限
3. 应用是否已加入该群或有访问权限

### Q: 写入多维表格失败

A: 检查以下几点：
1. 多维表格URL是否正确
2. 应用是否有多维表格的写入权限
3. 目标字段是否存在

## 技术支持

如遇到问题，请检查：

1. 配置文件是否正确填写
2. 应用权限是否完整
3. 日志文件中的错误信息
4. 网络连接是否正常

## 更新日志

- v1.0.0: 初始版本，支持基本的群成员获取和多维表格写入功能