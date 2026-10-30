# spec-orchestrate — 分层目录的全自动 ACSL 验证编排

> 对一个已分层的 C 项目目录执行逐层 Frama-C WP 验证：填充合约 → 派发子 Agent → 收集结果 → 处理失败。

## 触发条件

用户提供一个已分层的目录（由 `spec-split` 产出，或手动准备），要求对其中的函数进行 Frama-C WP 验证。

## 输入

一个符合以下结构的目录：

```
<DIR>/
├── contracts.json              # 合约库（可以是空骨架或含已验证合约）
├── layer0/
│   ├── func_a/
│   │   ├── func_a.c            # stub 切片（必需）
│   │   └── func_a.inline.c     # inline 参考（可选）
│   └── func_b/
│       └── ...
├── layer1/
│   └── ...
└── ...
```

**最小要求**：`contracts.json` + 至少一个 `layer<N>/<FUNC>/<FUNC>.c` 文件。

## 环境

```bash
PYTHONPATH=spectool python3 -m spectool.cli <command> [args]
```

## Phase 0: 状态检测与断点续做

skill 启动时先扫描目录，自动判断进度：

1. **扫描目录结构**：识别所有 `layer<N>/<FUNC>/` 目录
2. **读取 `contracts.json`**：检查每个函数的 status（`null` = 未开始，`"pass"` = 已验证，`"fail"` = 失败）
3. **检查 `.acsl.c` 产物**：已验证的函数应有 `<FUNC>.acsl.c` 文件
4. **确定起始层**：跳过所有函数都已 pass 的层，从第一个有未完成函数的层开始

```
状态检测结果示例：
  Layer 0: 4/4 pass ✓ (skip)
  Layer 1: 2/2 pass ✓ (skip)
  Layer 2: 0/1 pending → START HERE
  Layer 3: 0/1 pending
  Layer 4: 0/1 pending
```

如果全部已完成，直接生成 summary.json 并退出。

## Phase 1: 逐层验证（核心）

**严格按层执行：当前层全部完成后才开始下一层。**

同一层内的函数互不依赖，**可以并发执行**。

### 1.1 每层开始前：填充合约

```bash
PYTHONPATH=spectool python3 -m spectool.cli fill-contracts \
  --file <DIR>/layer<N>/<FUNC>/<FUNC>.c \
  --db <DIR>/contracts.json
```

自动将所有已验证的下层 callee 合约填入 stub 中的 `/* TODO */` 标记。跨层引用（如 L3 函数调用 L0 函数）也能正确填充，因为合约库是全局的。

未验证的 callee（同层或更高层）保留 `/* TODO */`，不影响当前验证。

**注意**：`fill-contracts` 在已填充的文件上运行可能产生重复声明。如果遇到此问题，直接手写 `.acsl.c` 文件而非依赖 fill-contracts。

### 1.2 派发子 Agent

每个子 Agent 启动时提供：

```
1. 待验证文件: <DIR>/layer<N>/<FUNC>/<FUNC>.c（已填充合约）
2. inline 参考: <DIR>/layer<N>/<FUNC>/<FUNC>.inline.c（供阅读理解行为，如果存在）
3. 输出目录: <DIR>/layer<N>/<FUNC>/
4. 产物命名: <FUNC>.acsl.c, <FUNC>.wp.txt
5. 指令: 严格按照 spec-bottomup skill 执行
6. WP timeout: 8s（默认）
```

**重要**：stub 文件中 `/* === Target: ... === */` 之前的内容（类型定义、宏、全局变量）是编译所需的头部。子 Agent 应跳过这些，只关注：
- Target 函数体（`/* === Target */` 之后）
- Dependency stub 声明及其合约（`/* --- Dependency */` 标记处）
- inline 参考文件中对应 callee 的实现（理解行为用）

子 Agent 不需要知道整体流程，只负责单个文件的验证。

### 1.3 每层完成后：收集合约

每个函数验证通过后，立即存入全局合约库：

```bash
PYTHONPATH=spectool python3 -m spectool.cli save-contract \
  --acsl <DIR>/layer<N>/<FUNC>/<FUNC>.acsl.c \
  --db <DIR>/contracts.json \
  --proved "N/N"
```

## Phase 2: 失败处理与鲁棒性

### admit 策略

- **前 3 轮修复期间**：不提及 admit，全力修复
- **第 3 轮仍失败时**：允许对 `\valid`/`\valid_read`/`\separated` 属性使用 `//@ admit`
- **绝对不允许**：admit 循环不变式、函数后置条件、用户断言

### 节点失败不阻塞整体

如果某个函数在 5 轮修复 + admit 后仍然无法验证：

1. 标记为 `FAILED`，保留最后一次最佳结果（proved 最多的版本）
2. 为该函数生成一个**保守合约**（只含 `assigns` 和 `ensures \result == 0 || \result < 0`）
3. 用保守合约存入 `contracts.json` — 上层仍然可以验证，只是信息较少
4. 记录失败原因到 `<DIR>/layer<N>/<FUNC>/FAILED.md`

### 合约加强回退

如果上层验证需要下层提供更强的后置条件：

1. 回到下层，尝试加强合约（如添加 `ensures *eaten <= \old(len);`）
2. 重新验证下层 — 确认加强后仍然通过
3. 更新 `contracts.json`（重新 `save-contract`）
4. 重新 `fill-contracts` 到上层 stub

## Phase 3: 生成 summary.json

所有层完成后，生成整体验证摘要：

```json
{
  "project": "<DIR>",
  "total_functions": 9,
  "verified": 9,
  "failed": 0,
  "layers": [
    {
      "layer": 0,
      "functions": [
        {"name": "func_a", "status": "pass", "proved": "24/24", "admits": 0},
        {"name": "func_b", "status": "pass", "proved": "70/70", "admits": 1}
      ]
    }
  ],
  "failed_details": [
    {"name": "func_x", "layer": 2, "best_proved": "18/22", "reason": "loop variant"}
  ],
  "total_proved_goals": 271,
  "total_admits": 7
}
```

## 可用的 spectool 命令

| 命令 | 用途 |
|------|------|
| `fill-contracts --file <STUB> --db <DB> [--out <PATH>]` | 用库中已有合约填充 stub 的 TODO |
| `verify --file <F> --timeout <N> --save-stdout <PATH>` | Frama-C WP 验证 |
| `locate-fail --wp <WP_OUT> --src <SRC>` | 定位失败 goals |
| `inject --src <F> --out <F> --func <F> --acsl <CONTRACT> --loops <JSON>` | 注入 ACSL 注解 |
| `save-contract --acsl <FILE> --db <DB> [--proved "N/N"]` | 验证通过后，将合约写入库 |
| `check-admit -f <FILE>` | 检查 admit 合规性 |

## 编排伪代码

```
1. 扫描 <DIR>，读取 contracts.json，确定起始层

2. for layer_num in start_layer..max_layer:
     # 2a. 填充已知合约
     for func in layers[layer_num].functions:
       if func.status != "pass":
         fill-contracts --file <DIR>/layerN/func/func.c --db contracts.json

     # 2b. 并发派发子 Agent
     for func in layers[layer_num].functions:
       if func.status != "pass":
         spawn_agent(spec-bottomup, input=<DIR>/layerN/func/)

     # 2c. 等待本层所有子 Agent 完成
     wait_all()

     # 2d. 收集合约到全局库
     for func in layers[layer_num].functions:
       if func.status == pass:
         save-contract --acsl func.acsl.c --db contracts.json --proved "N/N"

3. generate summary.json
```

## 注意事项

1. **contracts.json 是全局的**：所有层共用一个合约库。L3 函数调用 L0 函数时，合约从同一个库中取得
2. **子 Agent 上下文隔离**：每个子 Agent 只需知道自己的输入文件和 spec-bottomup skill 规则
3. **同层并发安全**：同层函数互不调用，文件互不重叠
4. **跨层严格串行**：必须等当前层全部完成并收集合约后，才开始下一层
5. **admit 只用于内存属性**：`\valid`/`\valid_read`/`\separated` — 参见 spec-bottomup skill 约束
6. **inline 文件是只读参考**：子 Agent 可以阅读 inline 文件理解函数行为，但验证目标始终是 stub 文件
7. **断点续做**：通过 contracts.json 的 status 字段判断进度，支持中断后继续
