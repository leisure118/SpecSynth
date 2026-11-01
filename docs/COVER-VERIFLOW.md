# VeriFlow 界面迁移说明

分支：`feat/cover-veriflow`。基础版本：`6ee11d6`。

## 复用范围

使用用户提供的 `VeriFlow-source-49f7912/ui` 为界面来源。`apps/web/src/styles/veriflow/` 保存原始 `home.css`、`home-overrides.css`、`projects.css`；仅将字体 URL 调整为本项目的 `/fonts/`。布局来源为 VeriFlow 的 `HomePage.tsx`、`ProjectsPage.tsx`，迁移到当前 Vue 路由和组件生命周期，而非加载另一套 React 应用或用 iframe 包住网站。Manrope 字体及其 OFL 许可证一并保留。

首页复用了导航、hero、技术栏、三步流程、案例区、原则区、底部 CTA 的布局结构。首屏替换为玄鉴已确认的 C/Rust 双轨 SVG 动效，随组件卸载释放动画帧与 ResizeObserver。项目页沿用 VeriFlow 的 heading/content 间距体系；工作台使用白色面板、紧凑边界和统一选择态。

`cover-veriflow.css` 是定制主题层。主色 `#9B5032`，正文 `#272A2E`，背景 `#FAF9F7`，边框 `#E4DFD9`。现有 CSS 中旧蓝紫品牌字面量同步收敛为中性色。代码语义颜色独立：spec 浅蓝、exec 浅绿、proof 浅橙。

## 功能与部署

保留现有 FastAPI、Vue Router、项目存储与 API。项目、导入、C 工作流、Rust NL2VBENCH、Agent/模型/Skill、运行进度、结果和历史继续使用 `/api/v1/`。没有迁入 VeriFlow 的 Go 后端、账号认证或私有配置，也没有引入个人 CLI、模型密钥或参考站的运行数据。

修复数据集“去验证”交接：打开新项目后直接进入 `rust-verify` 并打开参考源文件；生成入口保持独立任务页，不将参考实现冒充生成结果。

常规启动不变：安装项目依赖后 `npm run build:web`，再用项目 Python 环境启动后端。无需运行 3012 参考站，所有复用文件都在本仓库中。更新已有后端逻辑无需另一个前端框架运行时。

## 检查

```sh
npm run build:web
node --test tests/dataset-tree.cjs tests/verus-progress.cjs tests/verus-regions.cjs tests/workspace-render.cjs tests/workspace-run.cjs
.venv/bin/python -m pytest tests/test_web_assets.py tests/test_workspace_api.py tests/test_rust_workspace.py tests/test_rust_dataset.py tests/test_generation_agents.py tests/test_agent_deployment.py -q
ACSL_AGENT_TEST_BASE_URL=http://127.0.0.1:8010 PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/browser/cover-veriflow.spec.js
```

浏览器测试可用 `ACSL_AGENT_TEST_BASE_URL` 指定服务，避免本机 8000 已被其他应用占用。项目操作/Skill 等接口模拟测试应在独立静态预览上执行，测试数据仅存在浏览器拦截器内；不要对真实项目做破坏性回归。`dataset.spec.js` 与 `rust-workspace.spec.js` 使用全量 API 拦截。

## 环境限制

这次迁移没有补装项目内 Verus，也没有改变模型 API 或 C 容器工具链。接口模拟和案例回放通过不代表真实模型生成与验证已经端到端通过。当前本地 Verus 未就绪；X.509 函数详情依赖额外的 `x509-parser-bench` 与 `x509-parser-bench-splited/contracts.json` 数据包，缺失时接口返回 503。上述环境状态需与界面回归结果分开报告。

第三方源码沿用用户提供的使用授权；对外分发时应保留来源及原作者要求的署名/许可。这里不将 VeriFlow 的设计声明为从零原创。

## 本次检查结果

- 前端构建通过；5 组 Node 逻辑测试通过。
- 70 项 Python 回归通过（项目、Rust 数据集与工作流、Agent 部署、资源缓存）。
- 8 项全 API 模拟浏览器测试通过（独立静态端口 8128）。
- 5 项首页/手机导航/基准页浏览器测试通过（8010，只读或固定记录夹具）。
- 4 项已有 C 案例回放、旧链接、工件预览、结果页溢出检查通过。
- X.509 图谱能进入，但函数详情接口因本地证据包缺失返回 503；对应测试未通过。未进行真实模型生成与 Verus 验证，不将模拟或回放结果冒充真实执行。

浏览器测试修正了旧的控件定位和缺失夹具：配置区需先展开、Rust 文件需显式打开、任务页为自然语言文档、历史重跑记录使用固定夹具。项目下拉操作菜单改为原生可聚焦菜单，消除复制后浮层不稳定。
