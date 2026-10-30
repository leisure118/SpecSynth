# spec-bottomup — 自底向上 ACSL 规约生成

> 为单个 C 源文件自动生成可被 Frama-C WP 完全验证的 ACSL 注解（循环不变式 / loop assigns / loop variant / 函数契约）。

## 触发条件

用户提供一个 C 源文件（`.c`），文件中包含 `//@ assert(...)` 断言，要求生成能让 Frama-C WP 证明所有断言成立的 ACSL 注解。

## ⚠️ 硬性约束

### 1. 禁止翻阅无关资料

处理输入文件时，**只能读取你被明确告知的输入目录中的文件**。禁止：
- 搜索或浏览输入目录以外的任何文件夹
- 读取项目其他部分的代码或资料
- 查询网络或其他外部资源

只凭读入的 `.c` 文件本身的内容来完成 ACSL 生成。

### 2. 不得修改原始 assert

源文件中已有的 `//@ assert(...)` 断言，在注入后的 `.acsl.c` 中必须**完全保留原样**：
- 不可删除
- 不可修改断言表达式
- 不可改变断言位置

你可以额外添加辅助 `//@ assert(...)` 来帮助 Frama-C WP 推导（例如中间状态断言），但不能影响原始断言。

### 3. 产物输出规范

所有中间产物必须放在独立的子文件夹中。输出路径格式：
```
<输出目录>/<文件basename>/<文件basename>.acsl.c
<输出目录>/<文件basename>/<文件basename>.wp.txt
```

例如输入 `10.c`，输出目录为 `output/v2/`，则产物为：
```
output/v2/10/10.acsl.c
output/v2/10/10.wp.txt
```

### 4. Token 追踪

任务完成后，必须估算本 agent 消耗的 token 数并在 JSON 输出中记录。

### 5. 禁止执行无关命令

仅执行 inject → verify → locate-fail → 修复这条流水线所需的命令。**禁止运行**：
- `--help`、`-h` 查看帮助
- `--version` 检查版本
- `which`、`where`、`command -v` 查找工具路径
- `frama-c -config`、`alt-ergo --version` 等配置/版本查看命令
- `pip install`、`opam install`、`apt install` 等环境安装/更新
- 阅读 README、MANIFEST 或其他说明文件
- 任何非验证目的的 shell 命令

环境（frama-c 27.1、alt-ergo 2.6.2、spectool CLI）已完全就绪，直接执行验证流水线。

## 前提

运行环境中需要：
- `frama-c` 27.1 + `alt-ergo`（通过 opam 环境）
- spectool CLI（通过 `PYTHONPATH=spectool python3 -m spectool.cli`）

**环境激活命令**（所有 CLI 调用都可用这个前缀）：
```sh
PYTHONPATH=spectool python3 -m spectool.cli
```
（无需 `eval $(opam env ...)`，环境已就绪）

## 整体流程

```
Step 1: 读源码 → 理解程序语义
Step 2: 识别所有循环和断言 → 建立依赖关系
Step 3: 按自底向上顺序，为每个循环生成 ACSL 注解
Step 4: 调用 spectool inject 注入注解
Step 5: 读取注入后文件，确认原始 assert 未被修改
Step 6: 调用 spectool verify 验证
Step 6.5: 若 verify Pass → spectool check-admit 检查违规 admit → 有违规则进入修复
Step 7: 若失败 → spectool locate-fail 定位 → 修复 → 重试（最多 5 轮）
```

## Step 1：读源码，理解程序语义

读取完整 C 源文件，分析：
1. **变量声明**：类型（int/long long/数组/指针）、初始值
2. **循环结构**：每个循环的行号、循环变量、循环范围、循环体操作
3. **断言**：`//@ assert(...)` 断言的内容和位置（记录断言原文，后续不得修改）
4. **数据流**：哪些变量在哪些循环中被修改，循环之间的数据依赖

## Step 2：识别循环，建立处理顺序

### 2.1 列出所有循环

用 `spectool extract` 列出函数：

```sh
PYTHONPATH=spectool python3 -m spectool.cli extract --src <file.c>
```

输出示例：
```json
{"functions": [{"name": "main", "start_line": 1, "end_line": 33}], "count": 1}
```

### 2.2 确定处理顺序

自底向上原则：
- **内层循环先于外层循环**
- **前面的循环先于后面的循环**（因为后面循环可能依赖前面循环建立的数组状态）
- **被调用的函数先于调用者**

## Step 3：为每个循环生成 ACSL 注解

这是最核心的步骤。**必须为程序中的每一个循环都生成注解**，包括那些看起来"简单"或者只包含 assert 的循环。

### 3.1 每个循环必须包含的 ACSL 子句

每个循环注解**必须**包含以下四类子句：

1. **`loop invariant`（循环不变式）**：
   - 循环变量的范围：`loop invariant 0 <= i <= N;`
   - 数组内容的描述（如果循环修改了数组）：`loop invariant \forall integer j; 0 <= j < i ==> a[j] == j;`
   - 需要向后续循环传递的知识

2. **`loop assigns`（循环修改集）**：
   - 列出循环体中**所有**被修改的变量和数组范围
   - 格式：`loop assigns i, a[0 .. N-1];`
   - 如果循环只读不写数组，只列标量：`loop assigns i;`

3. **`loop variant`（循环变体，证明终止性）**：
   - 一个每次迭代严格递减且非负的整数表达式
   - 常见模式：`loop variant N - i;`（递增循环）、`loop variant i;`（递减循环）

### 3.2 ACSL 语法规则

**每条子句必须以分号 `;` 结尾。** 示例：

```c
/*@
  loop invariant 0 <= i <= N;
  loop invariant \forall integer j; 0 <= j < i ==> a[j] == j;
  loop assigns i, a[0 .. N-1];
  loop variant N - i;
*/
for (i = 0; i < N; i++) {
    a[i] = i;
}
```

### 3.3 常见循环模式与不变式

#### 模式 A：简单赋值循环

```c
for (i = 0; i < N; i++) { a[i] = expr(i); }
```

不变式：
```
loop invariant 0 <= i <= N;
loop invariant \forall integer j; 0 <= j < i ==> a[j] == expr(j);
loop assigns i, a[0 .. N-1];
loop variant N - i;
```

#### 模式 B：累加循环

```c
for (i = 0; i < N; i++) { sum = sum + a[i]; }
```

不变式：
```
loop invariant 0 <= i <= N;
loop invariant sum == <closed-form of partial sum>;
loop assigns i, sum;
loop variant N - i;
```

#### 模式 C：数组变换循环（读写同一数组）

```c
for (i = 0; i < N; i++) { a[i] = a[i] - i*i; }
```

不变式需要同时描述已处理部分和未处理部分：
```
loop invariant 0 <= i <= N;
loop invariant \forall integer j; 0 <= j < i ==> a[j] == <new_value(j)>;
loop invariant \forall integer j; i <= j < N ==> a[j] == <old_value(j)>;
loop assigns i, a[0 .. N-1];
loop variant N - i;
```

#### 模式 D：仅含断言的验证循环

```c
for (i = 0; i < N; i++) {
   //@ assert(a[i] == -1); 
   }
```

虽然循环体不修改变量，仍然需要注解：
```
loop invariant 0 <= i <= N;
loop assigns i;
loop variant N - i;
```

#### 模式 E：反向索引循环

```c
for (i = 0; i < N; i++) { b[N-i-1] = i; }
```

注意索引映射：
```
loop invariant 0 <= i <= N;
loop invariant \forall integer j; N-i <= j < N ==> b[j] == N-1-j;
loop assigns i, b[0 .. N-1];
loop variant N - i;
```

#### 模式 F：双倍索引循环

```c
for (i = 0; i <= N; i++) { a[2*i] = 0; a[2*i+1] = 0; }
```

用 `2*j` 和 `2*j+1` 分别描述不变式可能导致 WP 推导困难。**优选线性化的统一描述**：
```
loop invariant 0 <= i <= N+1;
loop invariant \forall integer j; 0 <= j < 2*i ==> a[j] == 0;
loop assigns i, a[0 .. 2*N+1];
loop variant N+1 - i;
```

#### 模式 G：条件赋值循环

```c
for (i = 0; i < N; i++) { a[i] = (i % 2); }
```

不变式需要精确描述条件表达式：
```
loop invariant 0 <= i <= N;
loop invariant \forall integer j; 0 <= j < i ==> a[j] == (j % 2);
loop assigns i, a[0 .. N-1];
loop variant N - i;
```

### 3.4 关键规则：跨循环知识传递

**当一个循环读取了前面循环写入的数组时，必须将数组内容的知识作为后续循环的不变式显式携带。** Frama-C WP 不会自动继承前序循环的后置条件。

示例：循环 1 写 `a[]`，循环 2 读 `a[]` 并写 `b[]`，循环 3 读 `a[]` 和 `b[]`：

```c
// 循环 1 的不变式中建立：a[j] == j
// 循环 2 必须携带：\forall j; 0 <= j < N ==> a[j] == j  （注意范围是 0..N，不是 0..i）
// 循环 3 必须携带：a[j] 和 b[j] 的知识
```

**为什么范围是 `0 <= j < N` 而不是 `0 <= j < i`？** 因为在后续循环中，前序循环已经完成执行，数组内容对所有索引 `0..N-1` 都已确定。

### 3.5 关键规则：admit 与 requires 的区分

> **🚫 `//@ admit` 仅限于内存相关声明（`\valid`、`\separated`）。逻辑前提条件必须用 `requires`，不得用 admit 绕过！**

`admit` 是公理性假设，Frama-C 直接接受不做验证。因此使用前必须回答：**这是 WP 无法推导的内存事实，还是函数的前提条件，还是直接跳过验证？**

#### 三种情况对照

| 场景 | 正确写法 | 说明 |
|------|----------|------|
| ✅ 内存事实 | `//@ admit \valid(p+(0..N-1));` | WP 无法从 `malloc` 自动推导指针有效性 |
| ✅ 前提条件 | `/*@ requires \forall i,j; 0<=i<=j<n ==> a[i]<=a[j]; */` | 函数需要输入有序数组，写在函数契约中 |
| 🚫 跳过验证 | `//@ admit ret == 0;` | 等于直接声明答案，绕过证明，是作弊 |

#### ✅ 允许的 admit：仅限内存属性

当程序通过 `malloc` 分配内存时，Frama-C WP 无法自动推导指针有效性和分离性。**这是 admit 的唯一合法用途**：

```c
long long *a = malloc(sizeof(long long)*N);
long long *b = malloc(sizeof(long long)*N);
//@ admit \valid(a+(0 .. N-1));
//@ admit \valid(b+(0 .. N-1));
//@ admit \separated(a+(0 .. N-1), b+(0 .. N-1));
```

- 每个 `malloc` 的指针需要一条 `\valid` 声明
- 如果有多个 `malloc` 指针，需要两两之间的 `\separated` 声明
- admit 必须是内存谓词：`\valid(...)` 或 `\separated(...)`

#### ✅ 正确做法：前提条件 → requires

当程序的行为需要依赖输入数据的某些性质时（如数组有序、整数非负等），这些是函数的前提条件，**必须写在函数契约的 `requires` 中**：

```c
/*@
  requires n >= 0;
  requires \forall integer i, j; 0 <= i <= j < n ==> a[i] <= a[j];
  assigns \nothing;
  ensures \result == -1 || (0 <= \result < n && a[\result] == key);
*/
int binary_search(int a[], int n, int key) {
    // 循环不变式和函数体内不需要再 admit 数组有序性
}
```

**为什么不能用 admit 代替？** `requires` 是契约的一部分——调用者需要保证它，被调用者可以利用它。而 `admit` 是无条件的假设，没有任何验证义务，放在函数体内等于绕过契约层直接声明事实。

#### 🚫 禁止的 admit：跳过验证

**严禁使用 admit 来断言程序逻辑值**：

```c
// ❌ 禁止：admit 函数返回值 → 跳过验证
int ret = func();
//@ admit ret == 0;
//@ assert ret == 0;

// ❌ 禁止：admit 数组内容
//@ admit a[i] == 42;

// ❌ 禁止：admit 数学关系
//@ admit sum == N*(N+1)/2;

// ❌ 禁止：admit 本应是 requires 的前提条件
int binary_search(int a[], int n, int key) {
    //@ admit \forall integer i, j; 0 <= i <= j < n ==> a[i] <= a[j];  // ❌ 这应该是 requires
    // ...
}
```

#### 🎯 判断标准

用以下三个问题决定该用 admit、requires、还是都不该用：

1. **这个性质是内存属性吗（指针有效/数组分离）？** → `admit \valid(...)` 或 `admit \separated(...)` ✅
2. **这个性质是函数输入需要满足的条件吗？** → 写在函数 `requires` 中 ✅
3. **这个性质可以直接证明某个 assert 吗？** → 说明它在作弊 🚫

**核心原则**：admit 的唯一作用是向 WP 提供无法从代码中推导的内存信息。所有逻辑性质（数组有序、变量范围、数学关系）要么通过 `loop invariant` 证明，要么作为函数 `requires` 声明。

### 3.6 关键规则：VLA 数组的 separated 声明

当程序在栈上声明多个变长数组（VLA）时，Frama-C 同样无法自动推导分离性：

```c
int a[N];
int b[N];
//@ admit \separated(a+(0 .. N-1), b+(0 .. N-1));
```

### 3.7 关键规则：无括号 for 循环的注解位置

对于没有花括号的单行循环体：

```c
for(i=0;i<S;i++)
    a[i]=((i-1)*(i+1));
```

注解必须放在 `for` 关键字**之前**，不能放在 `for(...)` 和循环体之间：

```c
/*@ loop invariant ...; loop assigns ...; loop variant ...; */
for(i=0;i<S;i++)
    a[i]=((i-1)*(i+1));
```

**这一点在使用 `spectool inject` 时已自动处理**——只需将 `line` 设为 `for` 关键字所在的行号。

## Step 4：注入注解

使用 `spectool inject` 将生成的注解注入源码。

### 4.1 准备 loops JSON

将所有循环的注解组织为 JSON 数组，每个元素包含 `line`（`for`/`while` 关键字在**原始源码**中的行号）和 `acsl`（注解文本）：

```json
[
  {"line": 13, "acsl": "loop invariant 0 <= i <= S;\nloop invariant \\forall integer j; 0 <= j < i ==> a[j] == (j-1)*(j+1);\nloop assigns i, a[0 .. S-1];\nloop variant S - i;"},
  {"line": 15, "acsl": "loop invariant 0 <= i <= S;\nloop assigns i, a[0 .. S-1];\nloop variant S - i;"}
]
```

**注意**：
- `line` 是 `for`/`while` 关键字在**原始文件**中的行号（1-based）
- ACSL 中的 `\forall`、`\valid` 等反斜杠在 JSON 字符串中需要转义为 `\\forall`、`\\valid`
- 多条子句用 `\n` 分隔

### 4.2 如果需要 admit 声明

`admit` 声明不是循环注解，需要直接写入源文件。两种方式：

**方式 A**：将 admit 作为 loops JSON 的一项，`line` 设为第一个使用这些指针/数组的循环行号（它会被插入到该行之前）：

```json
[
  {"line": 8, "acsl": "admit \\valid(a+(0 .. N-1));\nadmit \\valid(b+(0 .. N-1));\nadmit \\separated(a+(0 .. N-1), b+(0 .. N-1));"},
  {"line": 8, "acsl": "loop invariant 0 <= i <= N;\nloop assigns i, a[0 .. N-1];\nloop variant N - i;"}
]
```

**方式 B（推荐）**：先用文件编辑工具手动插入 admit 行，然后对修改后的文件运行 inject。

### 4.3 执行注入

```sh
PYTHONPATH=spectool python3 -m spectool.cli inject \
  --src <原始文件.c> \
  --out <输出目录>/<basename>/<basename>.acsl.c \
  --loops '<JSON数组>'
```

输出示例：
```json
{"ok": true, "out": "file.acsl.c", "injected_contract": false, "injected_loops": 3}
```

### 4.4 注入后检查

**必须读取注入后的 .acsl.c 文件**，确认：
- 每个循环前都有对应的注解块
- 注解位置正确（在 for/while 关键字之前）
- ACSL 语法看起来合理（分号、括号配对）
- **所有原始 `//@ assert(...)` 断言都保留原样，没有被修改或删除**
- 如果有新增辅助 assert，确保它们不影响原始断言的逻辑

## Step 5：验证

```sh
PYTHONPATH=spectool python3 -m spectool.cli verify \
  -f <输出目录>/<basename>/<basename>.acsl.c \
  --timeout 15 \
  --save-stdout <输出目录>/<basename>/<basename>.wp.txt
```

输出示例：
```json
{"result": "Pass", "proved": 9, "total": 9, "raw_result_type": "Pass_9_9", "stdout_file": "file.wp.txt", "elapsed_sec": 1.136}
```

### 结果解读

| result | 含义 | 下一步 |
|--------|------|--------|
| `Pass` | 所有 proof goals 全部证明 | 进入 Step 5.5 admit 合规检查 |
| `Fail` | 部分 goals 未能证明 | 进入 Step 6 修复 |
| `Invalid` | Frama-C 语法错误或中止 | 检查 ACSL 语法，重新注入 |
| `Unknown` | 无法判定 | 增加 timeout 或检查注解 |

## Step 5.5：admit 合规检查

**verify Pass 之后、宣布成功之前**，必须运行 admit 合规检查，确保没有使用 admit 绕过验证：

```sh
PYTHONPATH=spectool python3 -m spectool.cli check-admit \
  -f <输出目录>/<basename>/<basename>.acsl.c
```

输出示例：
```json
{"ok": true, "total_admits": 1, "valid_admits": 1, "illegal_admits": 0, "violations": []}
```

### 结果处理

| ok | 含义 | 下一步 |
|----|------|--------|
| `true` | 所有 admit 均为合法内存声明（`\valid`/`\separated`）或无 admit | **任务完成** |
| `false` | 存在违规 admit（逻辑断言、返回值、数学关系等） | 进入 Step 6 修复，按下述方式处理 |

### 违规 admit 的修复

当 `check-admit` 报告 `ok: false` 时，`violations` 数组列出了每条违规 admit 的行号和内容。**修复方向**：

1. **删除违规 admit 行**
2. **用正确的 ACSL 机制替代**：
   - 如果 admit 的内容是函数输入的前提条件 → 改为 `requires` 写在函数契约中
   - 如果 admit 的内容是可以从循环推导出的性质 → 加强 `loop invariant` 使 WP 能自动证明
   - 如果 admit 的内容是跨循环的数组知识 → 在后续循环的 `loop invariant` 中显式携带（参见 §3.4）
   - 如果 admit 的内容是函数返回值的等价性（如 `admit ret == ret2`）→ 需要通过更强的函数契约 `ensures` + 循环不变式链来建立等价性证明
3. **修改后重新 verify**，再次 check-admit，直到 `ok: true`

> ⚠️ 违规 admit 修复计入 Step 6 的 5 轮修复预算。如果修复后 verify 失败，继续正常的 locate-fail → 修复流程。

## Step 6：修复循环（最多 5 轮）

### 6.1 定位失败

```sh
PYTHONPATH=spectool python3 -m spectool.cli locate-fail \
  --wp <输出目录>/<basename>/<basename>.wp.txt \
  --src <输出目录>/<basename>/<basename>.acsl.c
```

输出示例：
```json
{
  "failures": [
    {"goal": "Assertion", "line": 12, "function": "main", "kind": "assert"},
    {"goal": "Loop invariant preservation", "line": 5, "function": "main", "kind": "loop_inv"}
  ],
  "count": 2
}
```

### 6.2 失败类型与修复策略

| kind | 含义 | 修复方向 |
|------|------|----------|
| `loop_inv` | 循环不变式无法保持/建立 | 不变式太强或遗漏了条件，调整不变式表达式 |
| `assert` | 断言无法证明 | 通常说明前序循环的不变式没有携带足够信息到断言位置。**但需先确认该 assert 是原始断言还是辅助断言**——原始断言不可修改，只可以通过加强不变式来证明 |
| `assigns` | 修改集不完整 | 检查循环体，补全 loop assigns |
| `ensures` | 函数后置条件失败 | 检查函数契约 |
| `loop_variant` | 循环变体非递减 | 检查变体表达式 |
| `illegal_admit` | check-admit 发现违规 admit | **删除违规 admit**，用 `requires` 或更强的 `loop invariant` 替代（详见 Step 5.5） |

### 6.3 常见修复模式

**失败：assert 未能证明**
→ 检查断言所依赖的数组/变量，确保前序循环的不变式中包含了这些信息，且范围是完整的（`0..N` 而非 `0..i`）
→ 如果 assert 是原始的，**不可以修改其内容**，只能通过加强前序循环的不变式来间接证明

**失败：loop invariant preservation**
→ 不变式在循环体执行一步后不再成立。可能原因：
  - 不变式中的数学表达式有误
  - 遗漏了对某个变量变化的描述
  - 数组索引范围错误

**失败：Timeout**
→ 可能原因：
  - 不变式过于复杂，prover 超时
  - 缺少 `\valid` 或 `\separated` 声明
  - 尝试增大 `--timeout`（如 30 或 60）

### 6.4 修复流程

1. 读取 `.acsl.c` 文件和失败信息
2. 分析失败原因
3. 修改注解（可以直接编辑 `.acsl.c` 文件，或重新 inject）
4. **确认原始 assert 未被修改**
5. 重新 verify
6. 如果仍有失败，重复以上步骤

## 输出规范

任务成功后，产出：

1. **`<输出目录>/<basename>/<basename>.acsl.c`**：带完整 ACSL 注解的 C 文件（原始 assert 全部保留）
2. **`<输出目录>/<basename>/<basename>.wp.txt`**：Frama-C WP 原始输出
3. **JSON 结果**（输出到 stdout，严格如下格式）：

```json
{
  "file": "FILENAME",
  "status": "pass" 或 "fail",
  ⚠️ **判定规则**：只有 `proved == total` 才可判定为 `"pass"`，否则**必须**判定为 `"fail"`。不可将 `proved < total` 的情况标记为 pass。
  "round": 完成的轮数,
  "proved": 证明的 goal 数,
  "total": 总 goal 数,
  "elapsed_sec": 总耗时秒数,
  "tokens": 估算的 token 消耗数,
  "error": null 或 错误描述
}
```

## 完整示例

### 输入：`example.c`

```c
int main(void) {
  int A[2048];
  int i;
  for (i = 0; i < 1024; i++) {
    A[i] = i;
  }
  //@ assert(A[1023] == 1023);
}
```

### Step 1-3：分析并生成注解

- 一个循环（第 4 行），递增赋值 `A[i] = i`
- 一个断言要求 `A[1023] == 1023`
- 循环不变式需要表达 `A[j] == j` 对已赋值部分成立

### Step 4：注入

```sh
PYTHONPATH=spectool python3 -m spectool.cli inject \
  --src example.c --out output/example/example.acsl.c \
  --loops '[{"line": 4, "acsl": "loop invariant 0 <= i <= 1024;\nloop invariant \\forall integer j; 0 <= j < i ==> A[j] == j;\nloop assigns i, A[0 .. 1023];\nloop variant 1024 - i;"}]'
```

### Step 5：验证

```sh
PYTHONPATH=spectool python3 -m spectool.cli verify \
  -f output/example/example.acsl.c --timeout 10 --save-stdout output/example/example.wp.txt
```

输出：`{"result": "Pass", "proved": 9, "total": 9, ...}` → 完成。

## 完整示例 2（多数组 + 跨循环依赖）

### 输入

```c
int main()
{
  int i;
  int N=100000;
  int a[N];
  int b[N];
  int c[N];
  for(i=0;i<N;i++) {
    a[i]=1;
    b[i]=2;
  }
  for(i=0;i<N;i++){
    c[i]=a[i]+b[i];
  }
  for(i=1;i<N;i++){
    //@ assert(c[i] >= 3);
  }
  return 0;
}
```

### 分析

- 三个 VLA 数组 `a`, `b`, `c` → 需要 `\separated`
- 循环 1 写 `a` 和 `b`
- 循环 2 读 `a` 和 `b`，写 `c` → 需要携带 `a[j]==1` 和 `b[j]==2` 的知识
- 循环 3 只有 assert → 需要携带 `c[j]==3` 的知识

### 方式 B 操作（推荐）

**先手动插入 admit 行**，在 `int c[N];` 之后加入：
```c
  //@ admit \separated(a+(0 .. N-1), b+(0 .. N-1), c+(0 .. N-1));
```

**然后 inject 循环注解**（注意：行号基于修改后的文件）：

```sh
PYTHONPATH=spectool python3 -m spectool.cli inject \
  --src modified.c --out output/example/result.acsl.c \
  --loops '[
    {"line": 9, "acsl": "loop invariant 0 <= i <= N;\nloop invariant \\forall integer j; 0 <= j < i ==> a[j] == 1;\nloop invariant \\forall integer j; 0 <= j < i ==> b[j] == 2;\nloop assigns i, a[0 .. N-1], b[0 .. N-1];\nloop variant N - i;"},
    {"line": 13, "acsl": "loop invariant 0 <= i <= N;\nloop invariant \\forall integer j; 0 <= j < N ==> a[j] == 1;\nloop invariant \\forall integer j; 0 <= j < N ==> b[j] == 2;\nloop invariant \\forall integer j; 0 <= j < i ==> c[j] == 3;\nloop assigns i, c[0 .. N-1];\nloop variant N - i;"},
    {"line": 16, "acsl": "loop invariant 1 <= i <= N;\nloop invariant \\forall integer j; 0 <= j < N ==> c[j] == 3;\nloop assigns i;\nloop variant N - i;"}
  ]'
```

### 验证结果

```json
{"result": "Pass", "proved": 36, "total": 36}
```

## 多函数处理

当文件包含多个函数时：

1. 用 `spectool extract --src file.c` 列出所有函数
2. **叶子函数（不调用其他自定义函数的）先处理**
3. 为叶子函数添加**函数契约**（`requires` / `ensures` / `assigns`）
4. 处理调用者时，可利用被调用者的契约

### 函数契约注入

```sh
PYTHONPATH=spectool python3 -m spectool.cli inject \
  --src file.c --out output/result.acsl.c \
  --func helper \
  --acsl "requires n >= 0;\nensures \\result >= 0;\nassigns \\nothing;"
```

## 易错点清单

1. **忘记为"只读循环"加注解**：即使循环体只有 assert，也必须加 `loop invariant` / `loop assigns` / `loop variant`
2. **跨循环知识丢失**：后续循环不会自动知道前序循环建立的数组状态，必须显式携带
3. **`\forall` 范围错误**：在后续循环中引用前序数组状态时，范围应该是 `0..N`（完成态），不是 `0..i`（进行态）
4. **缺少 `\separated` / `\valid`**：malloc 指针和多个 VLA 数组需要显式声明
5. **JSON 转义**：`\forall` 在 JSON 中是 `\\forall`，`\valid` 是 `\\valid`，`\result` 是 `\\result`
6. **loop assigns 不完整**：必须列出循环体修改的**所有**变量，包括循环变量本身
7. **整数溢出**：对 `long long` 类型的变量，不变式中使用 `integer` 类型（`\forall integer j`）避免溢出问题
8. **原始 assert 不可修改**：任何辅助 assert 都不能替代或修改原始断言的内容
9. **禁止翻阅外部目录**：只读输入文件，不查看其他目录的资料
