# 共创指南

## 本地启动

1. 克隆仓库，安装 Python 3.13、Node.js 18+ 和 Docker Desktop。
2. 创建虚拟环境并安装依赖：`python -m venv .venv`，激活后运行 `pip install -r requirements.txt`。
3. 运行 `npm ci`，再运行 `npm run build:web`。
4. 复制 `.env.example` 为 `.env`，按所用模型填写自己的密钥。
5. 运行 `python scripts/run_api.py`，打开 http://127.0.0.1:8000/ 。真实验证需要 README 中说明的 Docker 镜像和可访问的模型服务。

## 合作流程

- 每项改动使用独立分支，例如 `feat/file-editor` 或 `fix/project-validation`。
- 提交后推送分支，发起 Pull Request，说明问题、修改及验证结果，由另一位成员审阅。
- 合并前同步主分支并解决冲突。
- 密钥只保存在各自的 `.env` 中；本地项目、历史运行数据和旧发布包不提交。

## 检查

前端修改运行 `npm run build:web` 和 `node tests/workspace-render.cjs`。后端修改运行完整回归：

```sh
.venv/bin/python -m pytest -q
```

其中 `tests/test_architecture.py` 会检查分层依赖，`tests/test_application_services.py` 直接测试应用服务。外部 x509/OpenHarmony 数据集未安装时，对应测试会自动跳过。这些回归检查不代表真实模型与 Docker 全链路验证成功。
