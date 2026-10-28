# B3 知识库快照

这是从既有 B3 实验机械迁移的 **705 条 NL→Verus 参考记录**，不是新的测试集，也不是当前工作台跑出的验证结果。知识库运行只使用本目录，不依赖旧实验目录。迁移时未重新生成描述、重建向量或调用模型 API。后续生成器 API 接入已启用新任务的查询 embedding，见 [接入说明](../../../docs/GENERATOR-INTEGRATION.md)；这不会改写原索引。

## 文件与使用边界

| 文件 | 用途 |
| --- | --- |
| `metadata.json` | 保持原顺序的 705 条参考；原始字段不变，补充来源和许可 |
| `index.faiss` | 原样复制的 FAISS IndexFlatIP，705 × 3072 维 |
| `manifest.json` | 条数、来源、版本证据、文件 SHA256、索引格式与边界说明 |
| `licenses/` | 四个源项目、rag_verus 的 MIT 原文及 Anvil NOTICE |

离线关键词检索只用于工作流预览，**不是原 B3 的 embedding 检索**。复现向量检索需要为新查询生成与原索引相匹配的 embedding，并进行 L2 归一化后使用内积搜索。原 README 和构建脚本声明模型为 `text-embedding-3-large`；现有二进制能确认维度、向量数、内积索引和归一化，不能独立证明实际服务商或模型身份，所以 manifest 将 `embedding_model_verified` 标为 `false`。迁移没有读取旧配置。

部分参考是带规约的函数签名，或依赖原仓库的类型、辅助引理、模块上下文。历史字段 `verified_verus` 不代表每条都能单文件编译，也不代表已经使用工作台锁定的 Verus 版本重新验证。不要直接把整个知识库标记为“705 个当前验证通过示例”。

## 精确来源

| 记录 `source` | 数量 | 上游仓库 |
| --- | ---: | --- |
| `vest` | 67 | Vest |
| `vestexp` | 30 | Vest |
| `verismo` | 344 | VeriSMo |
| `anvil_fluent` | 29 | Anvil |
| `anvil_rabbitmq` | 47 | Anvil |
| `anvil_vreplica` | 9 | Anvil |
| `anvil_zookeeper` | 39 | Anvil |
| `ironkv` | 140 | IronKV |
| 合计 | **705** | Vest 97、VeriSMo 344、Anvil 124、IronKV 140 |

上游代码由 RVBench/RAGVerus artifact 提取为 `rag_verus/code/tasks/*/verified/*.rs` 片段，再由既有 B3 转换脚本反向生成自然语言描述。本次按 `sample_id` 把原索引元数据与 NL JSONL 连接，逐条核对描述和代码，并核对代码与本地 artifact 文件内容；未改写原描述、代码、签名或分类。

`source_file` 是相对于上游 `RVBench_artifact` 的原路径，不是用户电脑上的绝对路径，也不一定是原项目可直接访问的文件路径。原 Unix 文件名中的 Rust 泛型可能包含 Windows 不允许的字符，`source_snapshot_file` 记录本地 artifact 的对应清洗文件名；每条 `source_file_sha256` 是实际核对到的本地源文件原始字节指纹。

| 上游 | artifact README 声明的版本 | 保留声明 |
| --- | --- | --- |
| [Vest](https://github.com/secure-foundations/vest) | `73b74c5771973f545d8c08d9edafb63df2a2d4a4` | [MIT](licenses/vest-LICENSE) |
| [VeriSMo](https://github.com/microsoft/verismo) | `9864eacb7f2237762235dbd7e089a314a6449651` | [MIT](licenses/verismo-LICENSE) |
| [Anvil](https://github.com/anvil-verifier/anvil) | `20312b9c3a1b95b1a834e99210b6917948ebb3ae` | [MIT](licenses/anvil-LICENSE)、[NOTICE](licenses/anvil-NOTICE) |
| [IronKV](https://github.com/verus-lang/verified-ironkv) | `8f50beecb44f21f040c40a044ef1988c43763f45` | [MIT](licenses/ironkv-LICENSE) |
| [RVBench / RAGVerus artifact](https://github.com/GouQi12138/RVBench) | `rag_verus` 独立提交版本 unknown | [artifact 内 rag_verus MIT](licenses/rag_verus-LICENSE) |

以上版本来自本地 artifact README，不是本次重新检出并验证的 Git 提交。发布归档是 [Zenodo 15313495](https://zenodo.org/records/15313495)。其记录级许可本次未能联网确认，manifest 标为 `unknown`；论文的 CC BY 不能代替代码或混合语料的许可说明。

## 许可与归属范围

各条目的 `license: "MIT"` 指向所含上游代码片段的项目级许可，并不把生成描述、其他数据集或所有间接依赖一并重新许可为 MIT。分发这些代码或实质部分时需保留各自版权及许可声明；Anvil 的 NOTICE 还明确提示子组件可能适用独立条款。本目录保留相关原文，而不复制整个依赖树。

既有 B3 的 NL 描述是从代码反向生成的，不应宣称第三方源码由本项目原创。原描述的实际生成模型和逐条人工审查状态未独立确认；如需统一对外发布的数据集许可，仍需按实际使用范围补充审查。论文引用解决学术归因，不替代许可证义务。

本快照仅含上述外部来源，没有 `verus__` 来源组；这不等于完成了与所有当前/未来测试集的近重复或语义泄漏审计。参考检索不能把同一任务的标准答案当作独立参考，正式实验仍应记录并审查检索命中。

## 元数据和完整性契约

- 数组位置就是向量位置；不能独立排序、删除、插入或改写 `description` 后继续使用旧索引。
- 保留 `sample_id`、`description`、`function_signature`、`verified_verus`、`category`；新增 `id = sample_id`、`code = verified_verus`、`index_position` 及来源字段。
- `manifest.source_counts` 是 8 个来源分组；`repository_counts` 是 4 个项目汇总；`sources` 提供每组链接、版本与许可。
- `original_files` 包含原 metadata、index、NL JSONL、构建脚本、转换脚本及两份 README 的 SHA256。原文件路径以 B3 目录为基准，不包含本机路径。
- `metadata_sha256` 校验迁移后的 JSON 字节；`metadata_order_sha256` 是按顺序取 sample_id 后以 UTF-8、`ensure_ascii=False`、紧凑 JSON 编码计算的 SHA256。
- 原索引 SHA256：`57175e3691d1ebccc0ab11487abdaea468b6a7f5fce8e337eff9c471d6e02a6f`。

## 重新机械导入（仅维护者需要）

打包前可从项目根目录运行 `python scripts/import_b3_knowledge.py --verify`，仅用当前项目核对条数、来源、元数据与索引顺序、所有指纹和许可证副本，不需要旧实验目录。

正常使用和打包不需要旧项目。需要从原 B3 快照重新导入时，先在 PowerShell 中设定 `b3Source` 为旧 `experiment/b3` 目录；该脚本只读来源，不读取任何 config，不访问网络。

```powershell
# 从当前工作台项目根目录运行；把占位路径改为实际来源。
$b3Source = 'PATH-TO-EXISTING-B3'
New-Item -ItemType Directory -Path '.\data\knowledge\b3' -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $b3Source 'kb\index.faiss') -Destination '.\data\knowledge\b3\index.faiss'
python .\scripts\import_b3_knowledge.py --source-b3 $b3Source
```

导入器拒绝条数、来源分布、描述/代码映射或索引结构不符的快照。它不自动重新生成 embedding。升级知识库需要另行设计索引重建与版本管理，不能把新内容直接塞入这份历史索引。

工作流定位、修复预算及论文引用见 [B3-WORKFLOW](../../../docs/B3-WORKFLOW.md)。
