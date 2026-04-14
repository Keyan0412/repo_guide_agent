# trace_symbol

目标：定位 symbol 的定义、关键引用，以及最可能调用链。

可用工具：
- `search_symbol`
- `read_files`
- `search_keyword`

硬规则：
- 不要把 import 当作调用链
- 读取文件内容时只用 `read_files`，即使只看一个文件也传单元素 `paths`
- 不要因为重名而草率合并不同符号
- 找不到完整链路时，返回保守的部分链路并明确不确定性

示例：

输入问题：
- “train() 最终是从哪里被调用起来的？”

输出示例：
```json
{
  "symbol_name": "train",
  "definitions": [{"path": "src/train.py", "line": 12, "signature": "def train(config):"}],
  "references": [{"path": "src/main.py", "line": 48, "usage_role": "在主流程中调用 train(args)"}],
  "most_likely_call_chain": [
    {"path": "src/train.py", "symbol": "train", "role": "definition"},
    {"path": "src/main.py", "symbol": "train", "role": "reference"}
  ],
  "conclusion": "train 最可能由主入口 main.py 触发。",
  "uncertainties": []
}
```
