# VeriFast 官方 C 示例与测试

来源：[VeriFast 26.10 官方发行包](https://github.com/verifast/verifast/releases/tag/26.10)（f76012f）。源码及所需头文件以原始相对路径和字节保存于 `sources/`。上游许可见 [LICENSE.md](https://github.com/verifast/verifast/blob/26.10/LICENSE.md)，各文件原有版权和许可声明保留。

扫描发行包中 808 个常规 C 文件（另有两个 C 符号链接不单独计数），用本机 VeriFast 26.10 执行 `-safe_mode -enforce_annotations -c -json`。首轮每文件 15 秒，超时文件以 60 秒复查。未调用模型，未修改规约，也未运行源码程序。

数据集包含 342 个实际通过的 C 编译单元，其中 164 个案例携带本地头文件依赖。未执行链接验证，不代表整个多文件程序已验证。该口径不涵盖必须使用上游特殊选项、预处理步骤或外部工具链才能验证的项目。

`index.json` 保存可浏览和重跑的条目；`evidence/` 保存结果和日志摘要；`excluded.json` 记录其余 466 个文件的状态与原因。筛选后通过率 100% 不代表全量发行包通过率。
