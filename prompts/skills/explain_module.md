# explain_module

目标：解释模块职责、关键文件、关键符号和上下游关系。

可用工具：
- `get_file_tree`
- `read_files`
- `search_keyword`
- `search_symbol`

硬规则：
- 不要只根据目录名判断职责
- 读取文件内容时只用 `read_files`，即使只看一个文件也传单元素 `paths`
- 需要通过文件内容支持关键结论

示例：

输入问题：
- “解释一下 src/retriever 模块是做什么的。”

输出示例：
```json
{
  "module_path": "src/retriever",
  "module_role": "负责检索相关文档并向上游返回候选结果。",
  "key_files": [{"path": "src/retriever/base.py", "role": "抽象接口"}],
  "key_symbols": [{"name": "BaseRetriever", "type": "class", "role": "统一检索器接口"}],
  "upstream_dependencies": ["src/config.py"],
  "downstream_consumers": ["src/pipeline.py"],
  "uncertainties": []
}
```
