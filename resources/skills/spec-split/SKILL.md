# spec-split — 大型 C 项目切片与分层

> 对一个多文件 C 项目进行函数级切片和 DAG 分层，产出可直接交给 spec-orchestrate 验证的分层目录。

## 触发条件

用户提供一个 C 项目目录，要求为其中的函数生成分层切片，为后续 Frama-C WP 验证做准备。

## 输入

- 一个 C 项目目录（含一个或多个 `.c` 文件），如 `x509-parser-bench/`
- 可选：指定函数子集（默认处理全部函数）
- 可选：指定输出目录（默认 `<项目名>-layered/`）

## 输出

一个分层目录，结构如下：

```
<OUT_DIR>/
├── contracts.json              # 合约库骨架（所有函数注册，contract=null）
├── layer0/
│   ├── func_a/
│   │   ├── func_a.c            # stub 切片（callee 仅声明 + TODO 标记）
│   │   └── func_a.inline.c     # inline 切片（callee 含完整实现）
│   └── func_b/
│       └── ...
├── layer1/
│   └── ...
└── ...
```

这个目录可以直接作为 `spec-orchestrate` 的输入。

## 环境

```bash
PYTHONPATH=spectool python3 -m spectool.cli <command> [args]
```

## 核心概念

### 分层策略（Bottom-Up DAG）

函数按调用图的拓扑序分层：

- **Layer 0**：叶子函数（无项目内调用），最先验证
- **Layer N**：所有 callee 都在 Layer < N 的函数

验证时从 Layer 0 开始逐层推进，每层函数的 callee 合约已在前序层确认。

### 两种切片模式

| 模式 | 用途 | callee 处理方式 |
|------|------|-----------------|
| **stub** | Frama-C WP 验证目标 | callee 仅保留声明 + `/* TODO: add ACSL contract here */` 占位 |
| **inline** | LLM 阅读理解行为 | callee 包含完整实现体 |

**配合使用**：inline 提供实现细节供 LLM 理解行为，stub（带已生成的合约）提供 callee 接口保证供 LLM 推理。

### Stub 切片结构

```c
/* Auto-generated minimal verifiable slice */
/* Target function: parse_Time */
/* Mode: stub */

#include <stdint.h>
typedef uint8_t u8;
#define ...
typedef enum {...};

/* --- Dependency: parse_generalizedTime (stub) --- */
/* TODO: add ACSL contract here */
int parse_generalizedTime(...);

/* --- Dependency: parse_UTCTime (stub) --- */
/* TODO: add ACSL contract here */
static int parse_UTCTime(...);

/* === Target: parse_Time === */
int parse_Time(...) { ... }   // 目标函数完整实现
```

### Inline 切片结构

```c
/* Auto-generated minimal verifiable slice */
/* Target function: parse_Time */
/* Mode: inline */

#include <stdint.h>
typedef uint8_t u8;
#define ...
typedef enum {...};

// 所有依赖函数的完整实现（按调用序排列）
static u8 compute_decimal(...) { ... }
int parse_generalizedTime(...) { ... }
static int parse_UTCTime(...) { ... }

/* === Target: parse_Time === */
int parse_Time(...) { ... }   // 目标函数完整实现
```

## 流程步骤

### Step 1: 查看分层信息

```bash
PYTHONPATH=spectool python3 -m spectool.cli list-layers --project-dir <PROJECT>
```

输出示例：

```
## Layer 0 (41 functions)    ← 叶子函数
  compute_decimal
  get_length

## Layer 1 (21 functions)    ← 只调用 Layer 0 的函数
  parse_UTCTime -> [compute_decimal]
  get_identifier -> [_extract_complex_tag]

## Layer 2 (17 functions)
  parse_Time -> [parse_UTCTime, parse_generalizedTime]
  ...
```

根据输出决定验证范围（全部 or 指定子图）。如果用户指定了函数子集，只处理这些函数及其传递依赖所在的层。

### Step 2: 初始化合约库

```bash
PYTHONPATH=spectool python3 -m spectool.cli init-contracts \
  --project-dir <PROJECT> --db <OUT_DIR>/contracts.json
```

生成骨架 `contracts.json`，每个函数注册 layer/signature/callees，contract 为 null。可反复运行，已有的 contract 会被保留。

### Step 3: 生成切片

对每个待验证函数生成两个切片：

```bash
# stub 模式 — 验证目标
PYTHONPATH=spectool python3 -m spectool.cli slice \
  --project-dir <PROJECT> --func <FUNC> --mode stub \
  --out <OUT_DIR>/layer<N>/<FUNC>/<FUNC>.c

# inline 模式 — 供 LLM 阅读理解行为
PYTHONPATH=spectool python3 -m spectool.cli slice \
  --project-dir <PROJECT> --func <FUNC> --mode inline \
  --out <OUT_DIR>/layer<N>/<FUNC>/<FUNC>.inline.c
```

批量生成脚本示例：

```bash
# 从 list-layers 输出解析函数列表，逐个切片
PYTHONPATH=spectool python3 -m spectool.cli list-layers --project-dir <PROJECT> \
  | grep -E '^\s+\S' | awk '{print $1}' | while read func; do
    # 确定该函数所在的 layer（需要从 list-layers 输出中解析）
    PYTHONPATH=spectool python3 -m spectool.cli slice \
      --project-dir <PROJECT> --func "$func" --mode stub \
      --out "<OUT_DIR>/layer${LAYER}/${func}/${func}.c"
    PYTHONPATH=spectool python3 -m spectool.cli slice \
      --project-dir <PROJECT> --func "$func" --mode inline \
      --out "<OUT_DIR>/layer${LAYER}/${func}/${func}.inline.c"
  done
```

### Step 4: 编译验证（可选）

确认所有 stub 切片可以通过语法检查：

```bash
for f in <OUT_DIR>/layer*/*/*.c; do
  gcc -fsyntax-only -std=c99 -w "$f" 2>/dev/null || echo "FAIL: $f"
done
```

### Step 5: 输出摘要

输出分层统计：

```
Split complete:
  Project: x509-parser-bench
  Output:  x509-parser-bench-layered/
  Layers:  11
  Functions: 212
  Layer 0: 41 functions (leaf)
  Layer 1: 21 functions
  ...
```

## 注意事项

1. **切片是自包含的**：每个 stub/inline 文件可独立编译（`gcc -fsyntax-only`），包含所有必要的类型定义、宏、全局变量
2. **`contracts.json` 是全局的**：所有层共用一个合约库，后续 spec-orchestrate 会在此基础上填充已验证的合约
3. **inline 文件是只读参考**：后续验证时，inline 文件仅供 LLM 理解函数行为，不参与 Frama-C 验证
4. **函数子集模式**：如果只处理部分函数，需要包含所有传递 callee 以保证完整性
5. **已知限制**：
   - 递归调用链深度上限 50（超过会截断）
   - `DECL_*` 宏展开只支持 `##` token pasting 的第一个参数
   - 暂不支持跨目录多项目（`--project-dir` 指向单一平坦目录）
