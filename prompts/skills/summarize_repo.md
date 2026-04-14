# summarize_repo

目标：总结仓库用途、技术栈、主要目录、运行方式和项目形态。

可用工具：
- `get_file_tree`
- `read_files`
- `search_keyword`

硬规则：
- 先看目录，再看 README 和依赖文件，再下结论
- 不要只看 README
- 读取文件内容时只用 `read_files`，即使只看一个文件也传单元素 `paths`
- 如果 README 和代码冲突，以代码与配置为准
- 若证据不足，写入 `uncertainties`

示例：

输入问题：
- “请概括这个仓库的用途、技术栈和主要目录。”

期望输出特征：
- `likely_purpose` 是具体用途，不是空话
- `top_level_modules` 要列出目录及职责
- `run_commands` 优先收录 README 或 CLI 中真实出现的命令

输出示例：
```json
{
  "repo_name": "demo-repo",
  "likely_purpose": "用于分析陌生仓库结构并生成阅读路线的命令行工具。",
  "primary_language": "Python",
  "frameworks": ["Pydantic", "OpenAI SDK"],
  "project_type": "cli",
  "top_level_modules": [{"path": "src/", "role": "核心实现"}],
  "run_commands": ["repo-guide-agent summarize --repo /path/to/repo"],
  "key_evidence": ["README 描述该项目为仓库导览 Agent"],
  "uncertainties": []
}
```
