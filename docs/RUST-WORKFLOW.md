# Rust / Verus 项目

在“项目 → 新建项目”选择 **Rust / Verus**，上传 `.rs` 文件或文件夹，也可直接创建安全加一示例。原有 C / ACSL 项目保持兼容。

## 本机安装

安装项目 Python 依赖，然后运行：

```sh
python -m pip install -r requirements.txt
python scripts/install_verus.py
```

安装脚本下载官方 Verus `0.2026.01.10.531beb1`、核对 SHA256 并安装对应 Rust 1.92.0 工具链。支持 macOS Apple Silicon / Intel、Linux x86_64、Windows x64。工具存于被 Git 忽略的 `tools/verus/`。也可设置 `VERUS_EXECUTABLE` 指定同版本验证器。

## 两种模式

- **当前文件 Verus 验证**：选择 `.rs` 文件作为库入口，使用整个项目的不可变源码快照解析同目录模块。不调用模型。只有验证器正常退出、实际验证项大于零、错误数为零才显示通过。
- **自然语言生成与验证**：填写任务描述及接口，选择模型，生成一份独立 Verus 候选，失败后按设置追加 0–3 轮修复。每轮保存代码、提示词、服务报告用量与诊断。结果不会自动覆盖源码；点击“载入编辑器”后审阅、保存。生成模式的输入是任务描述及接口，不自动把当前文件改写或发送给模型。

任务历史绑定文件、模式、源码版本。修改代码后旧结果会标记为历史版本。刷新继续查看任务，服务重启中断的任务不会自动重新调用模型，已保存的轮次仍可查看。

## 模型与参考库

默认使用平台现有 `configs/models_config.yaml` 和本机 `.env` 配置，不向前端返回密钥。也可通过 `NL2VERUS_CONFIG` 指向原 NL2Verus 格式的私有 YAML，或在被忽略的 `runtime/rust-settings.json` 中设置 `config_path`。专用配置保留原工程的服务地址限制。

RAG 需要专用配置中的 `text-embedding-3-large`（3072 维）接口，使用随源码移植的 705 条参考及原 FAISS 索引。平台配置模式默认关闭 RAG，不以关键词检索冒充向量检索。“离线预览提示词”使用本地关键词检索，不调用模型。原数据集参考可以创建项目并重新验证，不被冒充为生成结果。

## 边界

本地单进程服务，未提供多用户隔离。Rust 使用 Verus 支持的语法及 vstd，不执行生成程序，不运行 Cargo/build.rs，不自动安装第三方 crate。选择文件作为库入口验证其可达模块，不等同于遍历所有未引用文件；每个独立文件可分别提交。暂不支持 `include!` / `include_str!` / `include_bytes!`、`#[path]` 和环境读取宏。

“验证通过”表示所提交规约通过 Verus 检查，不等于自然语言需求经过语义审核。明显 assume/admit/external_body 标记会被拦截，这不是完整可信代码审计。

## 接口

- 项目创建/保存增加 `language: C | Rust`，旧请求默认 C，项目创建后语言不可变。
- 项目提交模式增加 `rust-verify` / `rust-generate`，仍使用原 `/api/v1/projects/{id}/runs` 和 `/api/v1/runs/{id}` 结果接口。
- `GET /api/v1/rust/status`：验证器与脱敏模型能力。
- `GET /api/v1/rust/examples?q=&page=1`：原数据集参考。
- `POST /api/v1/rust/prepare`：离线提示词准备。
