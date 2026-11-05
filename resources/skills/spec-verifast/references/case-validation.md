# 案例验证与适用范围

本版本从原版三个 Skill 中保留依赖分层、调用者使用下层契约、循环知识传递和失败日志修复的方法；移除了其 Frama-C/spectool 命令、ACSL 固定模板、admit 兜底和未证明保守合约继续上层的做法。原版文件与版本记录不修改。

## 实际验收

使用项目的 `merge_spec_patches(..., verification_tool="verifast")` 和真实 VeriFast 26.10 运行器；验收参数保持 `-safe_mode -enforce_annotations -c -json`，未放松溢出检查、源代码锁定或独立验收。每次运行保存输入哈希、命令、原始输出和结果，证据在项目 runtime/verifast/<evidence_id>/。

从项目根目录复验：
```
.venv/bin/python resources/skills/spec-verifast/scripts/validate_cases.py --output runtime/skill-validation/spec-verifast-v1.json
```

| 案例 | 任务前提/目标 | 预期结果 |
| --- | --- | --- |
| count-loop.c | 给定 limit 范围，返回 limit；循环头与 `{` 同行 | 验证通过；3 statements |
| swap-pointers.c | 两个独立可写单元，交换值并归还权限 | 验证通过；3 statements |
| callee-first.c | 有界整数连续调用两次 plus_one | 验证通过；原生报告 1 statement |
| array-read.c | 两个数组单元的值与权限，返回和 | 验证通过；2 statements |
| ordinary-comment | 将函数契约改成普通注释 | 补丁静态检查拒绝 |
| acsl-mixed | 混入 loop invariant | 补丁静态检查拒绝 |
| wrong-contract-location | 契约放到签名前 | 实际 VeriFast 解析失败 |
| insufficient-invariant | 缺少 count <= limit | 实际 VeriFast 不能证明返回值 |
| missing-heap-permission | 只有指针非空，没有单元权限 | 实际 VeriFast 缺少 heap chunks |

这些 statement 数量是原生工具统计，不是函数数量或 ACSL proof goals；不从函数数反推分母。

测试过程发现并据此修改的规则：
- 数组规约原先绑定 ?x/?y，后续源码也声明 x/y，产生变量遮蔽错误：改为 ?vx/?vy，仅修改规约。
- helper 输入上界原先为 100000，不能证明 x+1 在所有当前配置允许的 int 范围内安全：案例任务限定为可移植的小范围；实际任务必须证明其真实输入范围，不能为通过随意缩窄前提。
- 计数循环原始缩进为四空格，`{` 在第 27 列：行列号由原始文本计算，不能复制其他案例的数字。

## 证据边界

这是人工准备的规约补丁经过真实验证器的案例回归，**没有调用线上主/子模型**，不能把 9/9 预期结果当作模型生成成功率。还需按实际模型运行任务，测量首次生成、最多 3 轮修复和人工继续修复的成功率。

复杂数组循环、动态内存分配、递归谓词、并发及终止性不在本轮已验证覆盖内。当前平台不支持新增 lemma 的补丁通道；遇到必须使用它们的任务应报告限制。

语法与模块化语义参考官方原始资料：
- [VeriFast C introduction](https://github.com/verifast/verifast/blob/master/intro-c.md)
- [Annotated C grammar](https://github.com/verifast/verifast-docs/blob/main/c_translation_units.md)
- [Release prelude predicates](https://github.com/verifast/verifast/blob/master/bin/prelude.h)
