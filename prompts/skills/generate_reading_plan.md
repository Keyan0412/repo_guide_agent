# generate_reading_plan

目标：围绕用户目标输出按顺序的阅读路线。

可用工具：
- `get_file_tree`
- `read_files`
- `search_keyword`

硬规则：
- 阅读顺序必须围绕目标，而不是把重要文件全部堆出来
- 读取文件内容时只用 `read_files`，即使只看一个文件也传单元素 `paths`
- 每一步都要说明为什么读它

示例：

输入问题：
- “如果我只想理解启动链路，应该按什么顺序读？”

输出示例：
```json
{
  "user_goal": "理解启动链路",
  "reading_steps": [
    {
      "order": 1,
      "path": "src/main.py",
      "why_read": "这里是程序入口，先建立启动主链路。",
      "focus_points": ["参数解析", "组件初始化"]
    },
    {
      "order": 2,
      "path": "src/agent/router.py",
      "why_read": "理解用户问题如何被转成执行计划。",
      "focus_points": ["意图解析", "plan 构建"]
    }
  ],
  "suggested_stop_condition": "能够说清用户输入如何一路流向具体 skill 执行。",
  "uncertainties": []
}
```
