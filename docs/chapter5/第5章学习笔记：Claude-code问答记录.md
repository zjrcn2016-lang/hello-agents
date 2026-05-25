# 第5章学习笔记：Claude-code 问答记录

> 本文档由 `/save-study-notes` 自动整理，记录学习过程中的核心问答。

---

## 目录

- [Q1: Dify 怎么部署](#q1-dify-怎么部署)
- [Q2: clone 速度慢怎么办](#q2-clone-速度慢怎么办)
- [Q3: Docker Hub 有什么用](#q3-docker-hub-有什么用)
- [Q4: 为什么 localhost 就行了](#q4-为什么-localhost-就行了)
- [Q5: Dify 怎么关闭](#q5-dify-怎么关闭)
- [Q6: Dify 中指令和查询有什么区别](#q6-dify-中指令和查询有什么区别)
- [Q7: MCP 资源、提示词作为工具是什么意思](#q7-mcp-资源提示词作为工具是什么意思)

---

## Q1: Dify 怎么部署

> **核心概念**：Dify 支持云端 SaaS 和本地 Docker 两种部署方式，本地部署用 Docker Compose 一键启动。

### 解答

**方式一：云端 SaaS（最简单）**

直接访问 dify.ai 注册账号即可，无需任何部署。

**方式二：本地 Docker 部署（推荐自托管）**

```bash
# 1. 克隆仓库
git clone --depth 1 https://mirror.ghproxy.com/https://github.com/langgenius/dify.git

# 2. 进入 docker 目录
cd dify/docker

# 3. 复制配置文件
cp .env.example .env

# 4. 启动所有服务
docker compose up -d
```

启动后访问 `http://localhost`，首次进入设置管理员账号，然后在设置 → 模型供应商中添加 API Key。

**包含的服务：**

| 服务 | 说明 |
|------|------|
| nginx | 反向代理，对外暴露 80 端口 |
| api | Dify 后端（Python） |
| web | Dify 前端（Next.js） |
| db | PostgreSQL 数据库 |
| redis | 缓存 |
| weaviate | 向量数据库 |

---

## Q2: clone 速度慢怎么办

> **核心概念**：使用国内镜像源或 `--depth 1` 参数可以显著提升 git clone 速度。

### 解答

**推荐组合：镜像源 + `--depth 1`**

```bash
git clone --depth 1 https://mirror.ghproxy.com/https://github.com/langgenius/dify.git
```

**其他方法：**

```bash
# 用 Gitee 镜像
git clone https://gitee.com/mirrors/dify.git

# 只拉最新一层（不下载完整历史，体积小很多）
git clone --depth 1 https://github.com/langgenius/dify.git

# 直接下载 zip（最快，不需要 git）
# GitHub 页面点 Code → Download ZIP
```

`--depth 1` 只拉最新提交，跳过完整 git 历史，速度快几倍。

---

## Q3: Docker Hub 有什么用

> **核心概念**：Docker Hub 是 Docker 官方镜像仓库，相当于镜像的"应用商店"，docker compose 启动时从这里拉取镜像。

### 解答

当运行 `docker compose up -d` 时，Docker 需要从 Docker Hub 下载各种镜像：

```
nginx:latest          ← 从 Docker Hub 下载
postgres:15-alpine    ← 从 Docker Hub 下载
redis:6-alpine        ← 从 Docker Hub 下载
langgenius/dify-api   ← 从 Docker Hub 下载
```

**类比：**

| 概念 | 类比 |
|------|------|
| Docker Hub | 应用商店（App Store） |
| 镜像（Image） | 安装包 |
| 容器（Container） | 运行中的应用 |
| `docker pull` | 下载安装包 |

**国内访问慢的解决方法：** 在 Docker Desktop → Docker Engine 中配置国内镜像加速：

```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me",
    "https://hub.rat.dev"
  ]
}
```

注意：登录 Docker Hub 账号和镜像下载是两回事，跑 Dify 不需要登录 Docker Hub。

---

## Q4: 为什么 localhost 就行了

> **核心概念**：Docker 将 nginx 容器的 80 端口映射到本机 80 端口，浏览器默认访问 80 端口，nginx 再反向代理到各服务。

### 解答

`http://localhost` 等价于 `http://localhost:80`，浏览器默认访问 80 端口所以可以省略。

`docker-compose.yaml` 里 nginx 的配置：

```yaml
nginx:
  ports:
    - "80:80"   # 本机80端口 → 容器80端口
```

**请求链路：**

```
浏览器 → localhost:80 → nginx容器 → dify-web / dify-api
```

nginx 作为反向代理，负责把请求转发给对应的服务。

---

## Q5: Dify 怎么关闭

> **核心概念**：用 `docker compose down` 停止并移除容器，`docker compose stop` 只暂停保留数据。

### 解答

```bash
cd D:\Dify\dify-main\docker

# 完全关闭（移除容器，保留数据卷）
docker compose down

# 只暂停（保留数据，下次快速启动）
docker compose stop

# 再次启动
docker compose start
```

---

## Q6: Dify 中指令和查询有什么区别

> **核心概念**：指令是 System Prompt，定义 Agent 角色和行为；查询是用户每轮输入的消息，通过 `{{query}}` 变量注入。

### 解答

在 Dify 里配置 Agent 时，两个字段的作用不同：

| 字段 | 作用 | 对应什么 |
|------|------|---------|
| **指令（System Prompt）** | 定义 Agent 的角色、能力边界、回答风格、输出格式 | 人设 Prompt 的全部内容 |
| **开场白** | 用户打开对话时看到的第一句话，引导用户输入 | 例如："你好！请告诉我你想去哪里？" |
| **查询（用户输入）** | 用户每次发送的消息 | 运行时动态传入，通过 `{{query}}` 占位符引用 |

**实际操作：**

把人设 Prompt 粘贴到 Dify 的"指令"输入框，Dify 会把它作为 `system` 消息发给模型，每轮对话都生效。

如果指令框里需要显式引用用户输入，在末尾加：

```
用户的问题是：{{query}}
```

---

## Q7: MCP 资源、提示词作为工具是什么意思

> **核心概念**：MCP 除工具（Tool）外还可暴露资源（Resource）和提示词模板（Prompt Resource），Dify 提供开关控制是否将这两类也作为工具暴露给 Agent。

### 解答

MCP 协议定义了三种能力类型：

| 类型 | 说明 | 高德 MCP 是否有 |
|------|------|----------------|
| **工具（Tool）** | 可调用的函数，如搜索、路径规划 | 有，核心能力 |
| **资源（Resource）** | 静态或动态数据，如文件、数据库记录 | 无 |
| **提示词（Prompt Resource）** | MCP Server 内置的 Prompt 模板 | 无 |

**Dify 的两个开关：**

- **MCP 资源作为工具**：开启后，MCP 暴露的 Resource 也会被 Agent 当工具调用。高德 MCP 没有 Resource，设 False。
- **MCP 提示词作为工具**：开启后，MCP 内置的 Prompt 模板可被 Agent 调用。高德 MCP 没有内置 Prompt，设 False。

对于高德地图 MCP，两个开关都设 False，直接用工具调用即可。

---

## 额外知识点

> 以下内容不属于本章节核心知识点，但在学习过程中涉及，供参考。

### E1: 什么是 Mintlify

> **知识类型**：工具使用

Mintlify 是一个**技术文档网站生成工具**，用 Markdown/MDX 写文档，自动生成带导航、搜索、代码高亮的网站。Dify 的官方文档 `docs.dify.ai` 就是用它搭建的。

**和其他文档工具对比：**

| 工具 | 特点 |
|------|------|
| Mintlify | 颜值高，配置简单，适合产品文档 |
| GitBook | 老牌，功能全 |
| Docusaurus | Facebook 出品，适合技术项目 |
| VitePress | Vue 生态，轻量快速 |

**收费情况：** 免费版支持无限页面、自定义域名，够个人项目和小团队用。付费版 Startup $150/月，主要增加多人协作权限管理和私有文档功能。

---

### E2: Docker Compose 常用命令

> **知识类型**：工具使用

```bash
# 启动所有服务（后台运行）
docker compose up -d

# 停止并移除容器（数据卷保留）
docker compose down

# 只暂停容器（不移除）
docker compose stop

# 恢复暂停的容器
docker compose start

# 重启所有服务
docker compose restart

# 查看运行状态
docker compose ps

# 查看日志（实时）
docker compose logs -f

# 查看某个服务的日志
docker compose logs -f api

# 更新镜像并重启
docker compose pull
docker compose up -d

# 进入某个容器的终端
docker compose exec api bash
```

**常用组合：**

| 场景 | 命令 |
|------|------|
| 第一次启动 | `docker compose up -d` |
| 日常关闭 | `docker compose stop` |
| 彻底清理重来 | `docker compose down -v`（`-v` 会删数据卷，慎用） |
| 更新到新版本 | `docker compose pull && docker compose up -d` |

---
