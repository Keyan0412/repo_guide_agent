# 与说明书的不同之处

## 1. 现在是 LLM 主导，但保留规则回退

说明书强调 Skill + 工具的受控执行。当前实现已经正式切到：

- `LLM Router` 负责问题到 skill 序列的规划；
- `LLM Skill Agent` 在每个 skill 内进行受限工具调用；
- 规则逻辑保留为 fallback，而不是主链路。

这样做的原因是：

- 更接近真正的 agent 行为；
- 能让模型按任务动态决定读哪些文件、搜哪些关键词；
- 同时保留可用的降级路径，避免接口异常时系统完全不可用。

## 2. Prompt 不再只是占位，而是 agent 行为约束的一部分

说明书建议把 Skill 设计与 prompt 解耦。当前项目仍保留 `prompts/` 目录，但 prompt 已经进入主执行链路：

- Router 使用 prompt 约束计划输出；
- 各 skill 的 prompt 约束工具使用顺序、禁止事项和输出 schema；
- Python 代码负责工具执行、上下文维护和 fallback。

不同点在于：当前 prompt 仍比较短，工程约束更多写在代码里，而不是把全部规程都堆进 prompt。

## 3. 直接实现了 5 个 Skill，而不是只做 3 个 MVP Skill

说明书建议第一阶段先做：

- `summarize_repo`
- `find_entrypoints`
- `trace_symbol`

当前实现额外包含：

- `explain_module`
- `generate_reading_plan`

这样做是为了让 Router 的多步编排可以直接闭环，而不是只做半套链路。

## 4. 工具层增加了安全限制

说明书主要关注仓库分析能力，没有展开敏感文件处理。当前实现额外做了安全收敛：

- `.env` 及类似敏感文件会被树扫描、搜索和读取统一屏蔽；
- tool executor 会阻止模型访问仓库外路径；
- 这样可以避免把本地密钥直接送入模型上下文。

这属于说明书里没有明确写出、但工程上必须补的约束。

## 5. 输出仍偏工程调试风格

当前 CLI 输出仍以结构化 JSON 和工具调用日志为主，而不是纯自然语言答案。

这是刻意保留的，因为它更适合：

- 调试 LLM 的工具调用行为；
- 观察证据链；
- 为后续评测与 failure case 记录提供基础。

如果后面要更产品化，可以再在 `response_formatter.py` 上加一层更自然的最终回答整理。
