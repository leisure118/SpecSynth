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

### 使用 Qwen3.5-4B 微调模型

模型选项 `qwen35-4b-ft` 对应 GPU 服务器上的 LoRA 微调服务，调用时始终使用这个模型名。Mac 本机运行 API 时，默认通过已有 SSH 转发访问 `http://127.0.0.1:18001/v1`；可用 `QWEN35_4B_API_BASE_URL` 覆盖。先检查 `curl http://127.0.0.1:18001/v1/models` 是否列出 `qwen35-4b-ft`，再启动项目并在模型选项中选择它。

### 使用 Qwen3.5-9B 微调模型

模型选项 `qwen35-9b-ft` 对应 GPU 服务器上的 9B LoRA 服务（GPU 1、服务器本机端口 8002）。在 Mac 新开终端并保持 SSH 转发运行：

**验证状态（2026-10-10）：当前 vLLM 0.31.0 服务虽列出并接受 `qwen35-9b-ft`，但多组确定性请求中，基座与 LoRA 的文本及 token logprobs 完全相同；4B 服务也复现此现象。因此不能把当前响应视为已确认应用微调权重。正在核查 LoRA 权重，并计划用 PEFT 合并后的独立权重服务验证。此前的 Frama-C `Pass` 只证明生成的规约，不证明 LoRA 已生效。**

```bash
ssh -p 8000 -N -L 18002:127.0.0.1:8002 test3@10.102.128.126
curl http://127.0.0.1:18002/v1/models
```

Mac 本机调用地址为 `http://127.0.0.1:18002/v1`，容器默认使用 `http://host.docker.internal:18002/v1`。可分别通过 `QWEN35_9B_API_BASE_URL` 和 `.env` 中的 `QWEN35_9B_DOCKER_BASE_URL` 覆盖。请求模型名须为 `qwen35-9b-ft`。服务器端的 `base_model_name_or_path` 是已失效的训练路径；目前服务使用 `/home/test3/Users/yuxingcai/data/qwen35/base/Qwen3.5-9B` 作为基座，尚未通过权重哈希证明它与训练时的基座完全相同。一次单函数实测获得 Frama-C `Pass`，但生成的 `max2` 契约较弱，`Pass` 不代表已证明完整的最大值语义。

### 使用独立的 Qwen3.5-9B mix64 实验模型

模型选项 `qwen35-9b-mix64` 使用服务器端口 `8003`，Mac 通过 SSH 转发端口 `18003` 调用；它与原有 `qwen35-9b-ft` 选项分别配置。`SCF-Qwen9B/training_output_mix64/adapter_model.safetensors` 与先前 9B 适配器的 SHA-256 一致，但先前的 vLLM LoRA 服务尚未证实应用微调权重。新服务应加载 PEFT 合并后的完整模型目录 `/home/test3/Users/yuxingcai/data/qwen35/merged/Qwen3.5-9B-mix64`，不使用 `--enable-lora`。请检查 `/v1/models` 中 `root` 指向该目录后再做批量实验。

Mac 新开终端并保持转发运行：

```bash
ssh -p 8000 -N -L 18003:127.0.0.1:8003 test3@10.102.128.126
curl http://127.0.0.1:18003/v1/models
```

Mac 本机 API 默认使用 `http://127.0.0.1:18003/v1`；Docker Compose 中的 autospec、termination 服务默认使用 `http://host.docker.internal:18003/v1`。可分别通过 `QWEN35_9B_MIX64_API_BASE_URL` 和 `.env` 中的 `QWEN35_9B_MIX64_DOCKER_BASE_URL` 覆盖。首次运行前，在容器中验证 `curl -fsS "$QWEN35_9B_MIX64_API_BASE_URL/models"`。GPU 1 的显存不足以保证原 9B 服务与新的完整 9B 服务按现有显存配置同时运行；先确认 GPU 空闲，保留旧端口配置供切换。

`single`、`inter-modular`、`batch` 和 `termination` 的实际分析由 Docker 容器执行。容器需要能访问模型 API；Compose 默认使用 `http://host.docker.internal:18001/v1`，也可在 `.env` 中用 `QWEN35_4B_DOCKER_BASE_URL` 指定一个容器可达的地址。当前 SSH 转发若只监听 Mac 的 `127.0.0.1`，容器不一定能通过 `host.docker.internal` 访问。运行完整分析前，先启动 Docker Desktop，并在容器中检查：

```bash
docker compose run --rm -T autospec bash -lc 'curl -fsS "$QWEN35_4B_API_BASE_URL/models"'
docker compose run --rm -T termination bash -lc 'curl -fsS "$QWEN35_4B_API_BASE_URL/models"'
```

如果容器访问失败，需要改用容器可达的模型地址，例如网关配置完成后的 `http://10.102.128.126:8001/v1`，并写入 `.env` 的 `QWEN35_4B_DOCKER_BASE_URL`。对统一容器版本可执行 `docker compose -f docker-compose.unified.yml exec acsl-agent sh -lc 'curl -fsS "$QWEN35_4B_API_BASE_URL/models"'` 做同样检查。模型生成的 ACSL 仍需通过项目原有的注入、Frama-C/WP 验证流程；模型能返回文本不代表规约正确。

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
