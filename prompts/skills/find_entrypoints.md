# find_entrypoints

目标：找出最可能的 1-3 个入口文件，并说明依据。

可用工具：
- `get_file_tree`
- `read_files`
- `search_keyword`

硬规则：
- 先利用 README、脚本命令和配置缩小范围
- 读取文件内容时只用 `read_files`，即使只看一个文件也传单元素 `paths`
- 不要把 `tests/`, `examples/`, `docs/` 优先当成主入口
- 仅在有真实文件证据时给高置信度

示例：

输入问题：
- “这个项目主入口在哪里？”

输出示例：
```json
{
  "entry_candidates": [
    {
      "path": "src/main.py",
      "entry_type": "cli",
      "confidence": 0.95,
      "reason": "文件中包含 main 入口、参数解析和核心组件初始化。",
      "supporting_evidence": ["src/main.py:80 if __name__ == \"__main__\""]
    }
  ],
  "recommended_first_read": ["src/main.py"],
  "uncertainties": []
}
```
