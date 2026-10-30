# ACSL AGENT

ACSL AGENT 是一个面向 C 程序的形式化规约自动生成与验证系统。当前提交版聚焦三个主模块：

- `single`：单函数分析
- `termination`：终止性验证
- `inter-modular`：多模块分析
- `spectool`：工具箱，支持函数提取、工程切片、大模型生成 ACSL、`admit` 检查与 Frama-C/WP 验证

## 目录说明

```text
ACSLAgent/
├─ apps/         前后端应用
├─ configs/      模型与 demo 配置
├─ engine/       规约生成、验证与终止性分析引擎
├─ resources/    演示样例与静态资源
├─ scripts/      启动与辅助脚本
├─ tests/        测试脚本
├─ README.md
├─ requirements.txt
├─ package.json
├─ docker-compose.unified.yml
└─ Dockerfile.unified
```

## 环境要求

- Python `3.13.x`
- Node.js `18+`
- Docker Desktop

根目录 `.env.example` 给出了环境变量模板。实际运行时需按所选模型平台配置密钥。

## 启动方式

安装依赖：

```powershell
python -m pip install -r requirements.txt
npm install
```

拉取镜像：

```powershell
docker pull junjiehu1905/autospec:latest
docker pull junjiehu1905/termination_analysis:latest
```

启动服务：

```powershell
python scripts/run_api.py
```

访问地址：

```text
http://127.0.0.1:8000/
```

如需重建前端静态资源：

```powershell
npm run build:web
```

## 功能说明

### single

对单个 C 文件生成 ACSL 函数契约与循环不变式，并执行形式化验证，输出验证状态与相关工件。

### termination

在部分正确性基础上生成 `loop variant`，完成终止性验证，并输出阶段性结果与证明证据。

### inter-modular

对多 `.c/.h` 文件工程执行跨模块分析，合并翻译单元后完成规约生成、验证与结果恢复。

## spectool 集成

`spectool` 的核心逻辑已迁入 `engine/spectool_core/`，并通过现有 FastAPI 服务暴露为 `/api/v1/spectool/*` 接口。前端导航中的“spectool”页面提供独立工具工作台，不影响原有 `single`、`termination` 和 `inter-modular` 任务链。

`spectool` 现在支持直接调用大模型生成 ACSL。页面中选择源码文件、函数和模型后，可通过“AI 生成”或“大模型生成并注入”自动生成函数契约与循环规约，并复用原有注入器生成带 ACSL 的源码。模型列表来自 `configs/models_config.yaml`，密钥按对应平台从 `.env` 中读取，例如 `qwen-turbo` 使用 `aliyun_API_KEY`。

### 服务器部署的模型与网络配置

项目不再默认连接开发电脑的代理、SSH 转发或 Docker Desktop 宿主机地址。复制 `.env.example` 并填写服务器配置：

- `XUANJIAN_AGENT_PROXY` 默认留空，直接访问模型服务；确实需要代理时填写服务器可达的代理地址。
- 微调模型使用对应的 `QWEN35_*_API_BASE_URL`；Docker 服务使用对应的 `QWEN35_*_DOCKER_BASE_URL`，填写容器可达的模型服务地址（以 `/v1` 结尾）。未配置地址的微调模型不能调用。
- 前后端同源部署无需额外跨域配置；分开部署时，在 `ACSL_AGENT_ALLOWED_ORIGINS` 中填写实际前端域名，多个以逗号分隔。
- Codex、Claude Code 的程序和认证，以及验证器，需要在服务器单独安装与配置。

模型选项及模型名保持不变。历史微调服务尚未证实加载 LoRA 权重；模型服务可访问、模型生成的规约通过验证，均不等于已确认微调权重生效。

spectool 的验证器固定使用 Docker 容器，不检测也不调用本机的 `frama-c`、`Alt-Ergo`、`Z3` 或 `veri-clang`。后端会探测现有 `docker-compose.yml` 中的 `autospec`、`termination` 服务，并在容器内执行 Frama-C/WP；上传与输出目录通过仓库挂载映射到容器内 `/app/runtime/spectool/`。可用状态可通过 `GET /api/v1/spectool/capabilities` 查询，其中 `verify_runner` 就绪时固定为 `container`，`container_service` 会显示实际服务名。

环境变量 `SPECTOOL_VERIFY_CONTAINER_SERVICES` 可调整容器探测与执行顺序，默认值为 `autospec,termination`。`SPECTOOL_FRAMAC`、`SPECTOOL_VERI_CLANG` 不参与 spectool 验证器选择。

## 运行产物

任务结果统一写入：

```text
runtime/runs/<task_id>/
```

其中包括：

- `task.json`
- `result.json`
- `artifacts/`

## 说明

- 本提交版源码包仅包含作品主体代码、配置、样例与脚本。
- 外部依赖、运行缓存和历史产物不包含在本目录中。
- 结果判定以系统实际生成的验证工件与 Frama-C/WP 输出为准。


## 历史基准实验结果

项目页提供 LiveFMBench 2025、LiveFMBench 2024 和 autobench 的实验结果入口。导入快照与源码、日志位于 `resources/benchmarks/`，随项目部署，不依赖下载目录。接口为 `/api/v1/benchmarks`、`/api/v1/benchmarks/{id}` 和 `/api/v1/benchmarks/{id}/file?file=...`；前端支持通过 `#/benchmarks/{id}?file=...` 直接定位文件。

汇总采用实验包 scripts 中的修正版报告（违规 admit 按失败计），逐文件目标通过率采用 results.csv。autobench 原始清单为 262 条、报告分母为 257，页面分别显示，保留全部记录；LiveFMBench 2024 为较早的 284 文件版本。历史结果不会自动触发模型调用或重新验证。更新快照可执行 `python scripts/import_benchmark_results.py <实验包目录>`。


### 原始基准源码

基准工作台已附带原始 C 源码，独立保存于 `resources/benchmarks/<id>/original/`，不覆盖实验规约代码或历史分数。可在代码区切换“原始源码 / 实验规约代码”，重跑配置会记录选中的输入版本。重新导入实验结果后，执行 `python scripts/import_benchmark_sources.py <dataset_test目录>` 补充原始源码索引。导入器按唯一文件名匹配，并兼容文件名中的直引号/弯引号差异；不会用近似文件名误配未找到的案例。


### Rust 工作台：Codex 与第三方 API

Rust 项目中选择「Agent API 生成与验证」，再独立选择 Agent、已配置模型与 Skill。Codex 使用平台独立运行时和 Responses API，不读取本机 Codex 登录信息。第三方端点必须实际支持 `/v1/responses`（包括流式响应）；只支持 Chat Completions 的端点应选择模型直连或内置 Harness。

通过「＋ API 模型」添加多个服务配置；下拉框选择的配置决定实际 Base URL、Model ID、协议与认证方式。使用「编辑当前 API」可以修改当前配置；编辑时 API Key 留空保留原值，明确切换「无需认证」会清除原密钥。Base URL 可填 `/v1`，完整的 `/chat/completions` 或 `/responses` 地址也会规范化为 Base URL。私有配置保存在忽略提交的 `runtime/generation-models.json`。

可将 Responses 配置设为默认模型，新 Rust 任务即默认使用 Codex 和该模型；已有任务保留之前的明确选择。默认英文 Skill 在 `skills/verus/verus-baseline/SKILL.md`，每次生成与修复都会加载其指令，并在运行记录中保存内容快照。RAG 仍需另行配置 embedding；生成结果由实际 Verus 验证器判断是否通过。

Rust 工作台的右侧分为运行、配置、历史三个页签。生成提交后自动切换至运行页；时间线记录准备、生成、Verus 检查及每轮修复的实际起止时间。完成后自动打开结果代码，并展示验证项、错误数、退出码、验证耗时和可展开的诊断。旧记录没有阶段时间时显示「—」，不推算阶段耗时。Skill 使用单选列表，旧内置短提示词不再作为可选 Skill 展示。

NL2VBench 文件浏览器按文件名前缀组织全部任务，VeriCoding 与 VerusBench 包含二级目录。目录接口只返回文件元数据，任务输入接口仅返回自然语言与函数接口。点击任务会打开输入标签；生成结果在独立代码标签自动显示，支持标签切换与关闭。关闭全部标签后显示任务选择引导，也可通过上传 TXT、Markdown、JSON、Rust 文件或新建自定义任务开始。

配置页使用右侧完整可用高度，只有内容实际超出时才滚动。常规模型面板不直接展示 API 地址，地址在编辑配置窗口查看。提交新运行后立即显示本次任务，历史文件的浏览不会替换进行中的进度。生成文件沿用数据集任务名或上传文件名（例如 `VerusBench_Diffy_brs1.verus.rs`），重复输出使用序号区分；原始文件名同时写入运行记录和生成产物。
