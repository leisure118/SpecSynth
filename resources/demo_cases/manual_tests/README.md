# 手动测试样例说明

本目录提供四个用于前端手动验证的 `.c` 文件，覆盖单函数分析与终止性验证两类场景。

这些文件已经接入 `configs/demo_cases.json`，页面中的“示例用例”可以直接点选对应条目。

## 文件列表

### 1. 单函数分析候选成功样例

- 文件：`single_success_counter.c`
- Demo ID：`manual_single_success_live`
- 用途：测试 `single` 模块的稳定成功链路
- 设计预期：验证状态为 `Pass`
- 当前配置：`replay`
- 回放结果文件：`single_success_counter_verified.c`
- 备注：当前成功样例已经固定为稳定回放版本

### 2. 单函数分析失败

- 文件：`single_fail_false_postcondition.c`
- Demo ID：`manual_single_fail_live`
- 用途：测试 `single` 模块的失败链路
- 设计预期：后置条件与程序行为矛盾，验证状态为 `Fail` 或 `Invalid`
- 当前复测：`Fail`
- 备注：当前环境下该样例已经能够稳定落入证明失败路径

### 3. 终止性验证成功

- 文件：`termination_success_verified.c`
- Demo ID：`manual_termination_success_live`
- 用途：测试 `termination` 模块的正常成功链路
- 特征：文件中已包含 `loop invariant`
- 设计预期：系统补入 `loop variant` 后，终止性验证通过
- 当前复测：`Pass`
- 备注：本轮成功闭合 `1 / 1` 个证明目标

### 4. 终止性验证失败

- 文件：`termination_fail_non_terminating_verified.c`
- Demo ID：`manual_termination_fail_live`
- 用途：测试 `termination` 模块的失败链路
- 特征：循环条件为 `y >= 0`，循环体执行 `y = y + 1`
- 设计预期：系统可能生成候选 `loop variant`，但 Frama-C 无法完成终止性证明，最终状态为 `Fail`
- 当前复测：`Fail`
- 备注：系统生成了 `loop variant y;`，但该表达式不会严格下降，因此终止性证明失败

## 使用方式

### 前端页面测试

- `single` 模块：
  - `manual_single_success_live`
  - `manual_single_fail_live`

- `termination` 模块：
  - `manual_termination_success_live`
  - `manual_termination_fail_live`

### 选择原则

- `single` 模块直接上传单个 `.c` 文件即可
- `termination` 模块建议上传已具备阶段一结果特征的文件，也就是文件中已经存在 `loop invariant`

## 本轮实测结论

- 单函数模块当前具备一个稳定成功回放样例与一个真实失败样例
- 终止性模块当前具备稳定的成功样例与失败样例

## 说明

- 本目录样例用于手动回归与界面联调
- 若环境切换到真实执行模式，最终结果仍以当前 Docker 与 Frama-C 工具链行为为准
