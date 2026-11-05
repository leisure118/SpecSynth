# 服务器本机部署（不使用 Docker）

运行拓扑为“浏览器 → 服务器 FastAPI → 服务器上的官方 Agent CLI / 验证器 → 模型服务”。CLI、Frama-C、VeriFast、Verus 都安装在服务器操作系统中，由后端直接启动进程。用户电脑只需要浏览器，不安装验证工具，也不持有模型密钥。

## 本机与服务器配置分离

本机实验使用 `python scripts/run_api.py --profile local`，Frama-C 与 VeriFast 在 Docker 中执行；本页的服务器命令始终带 `--profile server`，不探测 Docker。CLI 在 API 所在机器运行，Rust / Verus 保持已有原生执行路径。

两套公开配置分别位于 `configs/runtime/local.env` 和 `configs/runtime/server.env`，只包含工具运行方式。模型密钥仍由各环境的私有 `.env` 管理。即使服务器误带了本机的工具选择，显式 `--profile server` 也会覆盖它，不会改写密钥。

## 1. 准备服务器

建议使用 Linux x86_64。准备 Python 3.13+、Node.js >=24.9、npm；使用 Verus 时还需要 rustup 和 curl。上传源码，不复制开发机的 `.venv`、`node_modules`、macOS 可执行文件或个人 CLI 登录记录。

在项目根目录执行：

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
npm ci
npm run build:web
cp -n .env.example .env
python scripts/install_agent_runtime.py
```

主模型与子模型分别填写服务器可访问的 API 地址及密钥。Qwen 使用 `QWEN35_*_API_BASE_URL`，不使用 `*_DOCKER_BASE_URL`。

## 2. 安装服务器验证器

### Frama-C / WP

在服务器按其操作系统安装 Frama-C、Alt-Ergo 和 Z3，确保服务账号能找到 `frama-c`、`alt-ergo`、`z3`。为复现已有验收口径，应核对 Frama-C 和求解器版本；安装不同版本可能产生不同结果。

如果通过 opam 安装，交互式终端中的 `opam env` 不会自动作用于系统服务。把 opam 的 bin 目录加入服务 PATH，或通过 `SPECTOOL_FRAMAC` 设置 Frama-C 的完整路径，并保证求解器也位于 PATH。

### VeriFast

```sh
python scripts/install_verifast.py
```

安装器下载固定 26.10 官方发行包并检查 SHA-256，Linux 服务器支持 x86_64。默认安装到 `runtime/tools/verifast/`，也可独立安装：

```sh
python scripts/install_verifast.py --root /opt/xuanjian-tools/verifast
```

采用自定义位置时设置 `VERIFAST_BINARY=/opt/xuanjian-tools/verifast/verifast-26.10/bin/verifast`。系统依赖需按发行包要求准备，安装目录必须允许服务账号读取和执行。

### Verus

先准备 rustup 和 curl，再执行：

```sh
python scripts/install_verus.py
```

安装器安装固定官方发布包和所需 Rust 工具链。已有安装可通过 `VERUS_EXECUTABLE` 指定可执行文件。

## 3. 固定为本机调用

服务器 `.env` 使用：

```dotenv
ACSL_VERIFIER_RUNTIME=host
SPECTOOL_VERIFY_RUNNER=host
VERIFAST_RUNTIME=host
ACSL_AGENT_LOCAL_TOOLCHAIN=1
```

本机工具缺失时显示不可用，不自动调用 Docker。旧 AutoSpec 完整流水线还需要 veri-clang 等自身依赖；安装 Frama-C 不等于旧流水线的所有依赖均已准备好。常用 Agent 生成后独立验证路线不需要 AutoSpec 容器。

## 4. 检查并启动

```sh
python scripts/check_server.py --profile server
python scripts/run_api.py --profile server
```

依赖检查不调用模型、不打印密钥。只检查部分工具时可用 `python scripts/check_server.py --tools agents framac verifast`。

默认访问 `http://<服务器地址>:8000/`。由服务器进程管理器托管 API，不依赖交互式 SSH 会话；CLI 和验证器子进程由 API 按任务创建，不单独暴露终端端口。生产入口可通过服务器反向代理提供 HTTPS 和访问控制。

系统服务必须设置项目工作目录、服务器虚拟环境 Python、可用的 PATH 和配置文件位置。Node.js 若由 nvm 安装，也需要显式加入服务 PATH；仅在 SSH 终端能运行不代表服务账号能运行。

## 数据、升级与验收

- `.env` 和 `runtime/generation-models.json` 仅存于服务器，不提交 Git，也不发送给浏览器。
- 备份 `runtime/` 中的项目、任务、Skill、人工版本和日志；可重新下载的工具与业务数据区分管理。
- 使用单 API worker。当前 JSON 存储与进程内队列不提供多节点调度。
- 升级先停止新任务，等待在途任务结束或请求取消并确认终态，再更新代码、构建前端和重启 API。
- 取消会阻止后续步骤；已经发出的模型调用可能仍计费并到自身超时才结束。重启后不自动重发历史模型请求。
- 最终需要在目标服务器完成依赖检查、直接验证案例和实际生成任务验收。本机通过不代表目标服务器已经安装成功。本次未实际上传或安装服务器工具。
