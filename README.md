# Repo Guide Agent

用于快速理解陌生代码仓库的 Skill-based Agent。

## 功能

- 仓库概览
- 入口定位
- 模块解释
- 符号追踪
- 阅读路线生成

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 百炼 / OpenAI 兼容调用

默认通过 OpenAI Python SDK 调用百炼兼容接口：

```bash
export OPENAI_API_KEY=your_bailian_api_key
export OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export OPENAI_MODEL=qwen-plus
export ENABLE_THINKING=false
```

程序启动时会自动加载仓库根目录下的 `.env`。

当前默认执行模式为：

- `LLM Router` 先规划 skill 序列
- `LLM Skill Agent` 在每个 skill 内进行受限工具调用
- `LLM Response Formatter` 将结构化结果转成自然语言

注意：

- 系统已不再保留规则 fallback
- 只要 LLM 在语义解析、skill 执行或最终输出任一阶段失败，程序会直接报错并中断

## 使用

```bash
repo-guide-agent --repo /path/to/repo --question "这个仓库是干什么的？"
repo-guide-agent --repo /path/to/repo --question "train() 最终是从哪里被调用起来的？"
repo-guide-agent --verbose --repo /path/to/repo --question "如果我只想理解启动链路，应该按什么顺序读？"
```

`--verbose` 会把 Router 规划、当前 Skill、LLM 等待状态和工具调用过程持续输出到 `stderr`，方便定位卡住的位置。

默认情况下，CLI 最终会输出更易读的自然语言说明；原始结构化 JSON 会自动保存到 `outputs/` 目录中。

## 使用方式

现在 CLI 只有一种交互方式：直接提自然语言问题。

例如：

- 想看仓库总览：
  `repo-guide-agent --repo /path/to/repo --question "这个仓库是干什么的？"`
- 想找主入口：
  `repo-guide-agent --repo /path/to/repo --question "这个项目主入口在哪里？"`
- 想解释模块：
  `repo-guide-agent --repo /path/to/repo --question "src/retriever 模块是做什么的？"`
- 想追踪 symbol：
  `repo-guide-agent --repo /path/to/repo --question "train() 最终是从哪里被调用起来的？"`
- 想要阅读路线：
  `repo-guide-agent --repo /path/to/repo --question "如果我只想理解启动链路，应该按什么顺序读？"`

也就是说，用户不需要再区分 `summarize`、`ask` 或 `trace`。所有问题都统一走：

- `QueryParser` 解析意图和槽位
- `Router` 构造 skill 执行计划
- `Executor` 驱动一个或多个 skill 完成分析
