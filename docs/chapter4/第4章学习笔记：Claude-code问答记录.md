# 第4章学习笔记：Claude-code 问答记录

> 本文档由 `/save-study-notes` 自动整理，记录学习过程中的核心问答。

---

## 目录

- [Q1: Plan-and-Solve 规划模型是什么意思？](#q1-plan-and-solve-规划模型是什么意思)
- [Q2: Planner 是不是很适合做 Chain-of-Thought？](#q2-planner-是不是很适合做-chain-of-thought)
- [Q3: ReAct 和 CoT 的区别](#q3-react-和-cot-的区别)
- [Q4: ReAct 中"观察"是怎么实现的](#q4-react-中观察是怎么实现的)
- [Q5: 为什么只思考了两轮就结束了，而不需要到最大步长](#q5-为什么只思考了两轮就结束了而不需要到最大步长)
- [Q6: LLM 是怎么确定是 Finish 的](#q6-llm-是怎么确定是-finish-的)
- [Q7: observation 是不是可以看到整个网页的信息](#q7-observation-是不是可以看到整个网页的信息)
- [Q8: Reflection 机制](#q8-reflection-机制)
- [Q9: 怎么写一个 ReAct 的计算器工具](#q9-怎么写一个-react-的计算器工具)

---

## Q1: Plan-and-Solve 规划模型是什么意思？

> **核心概念**：Plan-and-Solve 是一种"先规划、再执行"的智能体范式，将复杂任务拆分为规划阶段和执行阶段。

### 解答

Plan-and-Solve 是一种让智能体"先规划、再执行"的范式，核心思想是把一个复杂任务拆成两个独立阶段：

**阶段一：规划（Plan）**

把任务交给 LLM，让它输出一个分步骤的行动计划，而不是直接给答案。例如：

```
任务：华为最新手机有哪些卖点？

计划：
步骤1：搜索华为最新手机型号
步骤2：搜索该型号的主要功能特点
步骤3：整合信息，总结卖点
```

**阶段二：执行（Solve）**

按照计划逐步执行，每一步可以调用工具（搜索、计算等），把上一步的结果带入下一步。

**和 ReAct 的区别**

| | ReAct | Plan-and-Solve |
|---|---|---|
| 思考方式 | 边想边做，每步动态决策 | 先想清楚再做，按计划执行 |
| 适合场景 | 探索性任务，路径不确定 | 结构清晰的多步骤任务 |
| 风险 | 可能走弯路、反复试错 | 计划一旦有误，后续全错 |

**直觉类比：** ReAct 像边走边看地图，Plan-and-Solve 像出发前先规划好完整路线再开车。

---

## Q2: Planner 是不是很适合做 Chain-of-Thought？

> **核心概念**：Plan-and-Solve 是 CoT 的"可执行版本"——Planner 生成的计划本质上是结构化的 CoT，但 Solver 会真正调用工具执行，而不只是靠模型推理。

### 解答

有相似之处，但不完全一样。

**相似点：** 两者都是让模型"先拆解、再回答"，而不是直接输出结果。

**本质区别：**

| | Chain-of-Thought | Plan-and-Solve |
|---|---|---|
| 发生在哪里 | 单次 LLM 调用内部，模型自己推理 | 跨多次调用，有真实的工具执行 |
| 能否调用工具 | 不能，纯文本推理 | 能，每步可以搜索、计算等 |
| 输出是什么 | 推理过程 + 最终答案 | 计划 + 每步的真实执行结果 |

**CoT 的类比：** 让一个人在脑子里把解题步骤想清楚再写答案。

**Plan-and-Solve 的类比：** 让一个人先写下待办清单，然后真的去做每一件事，每件事完成后再做下一件。

所以可以说：**Plan-and-Solve 是 CoT 的"可执行版本"**。Planner 生成的计划本质上就是一段结构化的 CoT，但后续的 Solver 会真正调用工具去验证和补充信息，而不只是靠模型自己"想"出来的知识。

在实际项目里，两者也经常组合用——Planner 用 CoT 提示词让模型生成更高质量的计划，Solver 再逐步执行。

---

## Q3: ReAct 和 CoT 的区别

> **核心概念**：CoT 是一次性推理链，ReAct 是推理与工具调用交替进行的循环机制。

### 解答

**CoT（Chain of Thought）**

单纯的推理链，模型在回答前先"想一想"，但整个过程是一次性的，不会根据结果调整行动。

```
问题 → 思考步骤1 → 思考步骤2 → 最终答案
```

**ReAct（Reasoning + Acting）**

推理和行动交替进行，每次行动后观察结果，再决定下一步。

```
问题 → 思考 → 行动（调用工具）→ 观察结果 → 思考 → 行动 → ... → 最终答案
```

**对比：**

| | CoT | ReAct |
|---|---|---|
| 能否调用工具 | 否 | 是 |
| 能否根据结果调整 | 否 | 是 |
| 适合场景 | 数学推理、逻辑题 | 需要查询外部信息的任务 |
| 执行方式 | 一次生成 | 多轮循环 |

简单记：CoT 是"想清楚再说"，ReAct 是"边做边想，做完再看结果"。智能体框架基本都用 ReAct，因为需要和工具、环境交互。

---

## Q4: ReAct 中"观察"是怎么实现的

> **核心概念**：Observation 不是独立动作，而是工具执行后的返回值，写入 history 传给下一轮 LLM。

### 解答

"观察"不是一个独立的动作，它就是**工具执行后的返回值**，然后被写入 history 传给下一轮 LLM。

核心代码：

```python
tool_function = self.tool_executor.getTool(tool_name)
observation = tool_function(tool_input)   # 执行工具，返回值就是 observation

self.history.append(f"Action: {action}")
self.history.append(f"Observation: {observation}")  # 写入历史
```

**完整流程：**

```
第N轮：
  LLM 输出 → Thought: 我需要搜索华为手机
              Action: Search[华为最新手机]

  代码解析 Action → 找到工具函数 → 调用 search("华为最新手机")

  search() 返回字符串 → 这就是 observation

  把 "Observation: xxx" 追加到 history

第N+1轮：
  把整个 history 拼进 prompt → LLM 看到上一步的观察结果 → 继续思考
```

Observation 的内容完全取决于工具函数返回什么。LLM 自己不产生 observation，它只是读取工具执行后的结果。

---

## Q5: 为什么只思考了两轮就结束了，而不需要到最大步长

> **核心概念**：max_steps 是上限保护，LLM 判断信息足够时随时可以输出 Finish 提前结束。

### 解答

因为第二轮 LLM 认为已经有足够信息回答问题了，直接输出了 `Finish[最终答案]`。

```python
if action.startswith("Finish"):
    final_answer = self._parse_action_input(action)
    print(f"🎉 最终答案: {final_answer}")
    return final_answer  # 直接返回，退出 while 循环
```

**两轮的典型流程：**

```
第1轮：
  Thought: 我需要搜索华为最新手机
  Action: Search[华为最新手机]
  Observation: 华为Mate70，主要卖点是...

第2轮：
  Thought: 搜索结果已经包含了答案
  Action: Finish[华为最新款是Mate70，卖点是...]  ← 触发提前退出
```

`max_steps=5` 是**上限保护**，防止 LLM 陷入死循环或一直找不到答案时无限运行。只要 LLM 觉得够了，随时可以 `Finish` 提前结束。

---

## Q6: LLM 是怎么确定是 Finish 的

> **核心概念**：LLM 通过 Prompt 中的指令学会何时用 Finish，代码只做字符串匹配。

### 解答

LLM 是通过 **Prompt 里的指令**学会什么时候用 `Finish` 的：

```
Action: 你决定采取的行动，必须是以下格式之一：
- `{tool_name}[{tool_input}]`：调用一个可用工具。
- `Finish[最终答案]`：当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在`Action:`字段后使用 `Finish[最终答案]` 来输出最终答案。
```

每一轮 LLM 收到的 prompt 包含完整 history，它会自己判断问题是否已经可以回答。

**代码侧只是字符串匹配：**

```python
if action.startswith("Finish"):  # 判断 LLM 输出的字符串是否以 Finish 开头
```

"何时结束"是 LLM 的判断，代码只是识别 LLM 的输出格式。Prompt 写得越清晰，LLM 判断越准确。

---

## Q7: observation 是不是可以看到整个网页的信息

> **核心概念**：observation 是 Tavily API 处理后的摘要，不是完整网页，避免超出 token 限制。

### 解答

不是整个网页，而是 Tavily 处理后的**摘要信息**。

返回逻辑：

```python
response = client.search(query=query, search_depth="basic", include_answer=True)

# 优先返回 Tavily 综合后的直接答案（一段话）
if response.get("answer"):
    return response["answer"]

# 没有直接答案则返回前三条结果的标题+摘要
snippets = [...][:3]
```

| 情况 | 返回内容 |
|------|---------|
| Tavily 能综合出答案 | 一段精炼的直接答案 |
| 没有直接答案 | 前3条搜索结果的标题 + 内容摘要 |

完整网页内容可能几万字，全塞进 LLM 的 context 会超出 token 限制，而且大量无关内容会干扰 LLM 判断。

---

## Q8: Reflection 机制

> **核心概念**：Reflection 让智能体评估自己的输出质量，发现问题后自我修正，相当于让模型做自我 code review。

### 解答

Reflection（反思）机制是让智能体在行动后**评估自己的输出质量**，发现问题后自我修正。

**和 ReAct 的区别：**

```
ReAct:      思考 → 行动 → 观察（外部工具结果）→ 思考 → ...
Reflection: 行动 → 生成结果 → 反思（评估结果好不好）→ 修正 → 再反思 → ...
```

**基本实现思路：**

```python
class ReflectionAgent:
    def run(self, question):
        answer = self.llm.generate(question)

        reflection_prompt = f"""
        问题：{question}
        当前答案：{answer}
        请评估：1. 是否完整？2. 有无逻辑错误？3. 如何改进？
        """
        reflection = self.llm.generate(reflection_prompt)

        if "需要改进" in reflection:
            answer = self.llm.generate(f"根据以下反思改进答案：{reflection}")

        return answer
```

**实际应用场景：**

| 场景 | 反思内容 |
|------|---------|
| 代码生成 | 检查代码有没有 bug、边界情况 |
| 文章写作 | 评估逻辑是否连贯、论点是否充分 |
| 数学推理 | 验证计算步骤是否正确 |

核心思想是**用 LLM 评估 LLM 的输出**，通常能显著提升复杂任务的质量。

---

## Q9: 怎么写一个 ReAct 的计算器工具

> **核心概念**：在 tools.py 中定义工具函数，用正则白名单防注入，再注册到 ToolExecutor 即可被 ReAct 调用。

### 解答

分两步：定义工具函数 + 注册到 ToolExecutor。

**第一步：在 tools.py 中定义 calculate 函数**

```python
def calculate(expression: str) -> str:
    try:
        # 只允许数字和数学运算符，防止代码注入
        if not re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', expression):
            return "错误：只允许数字和 + - * / ( ) 运算符"
        result = eval(expression)
        return str(result)
    except ZeroDivisionError:
        return "错误：除数不能为零"
    except Exception as e:
        return f"计算错误: {e}"
```

**第二步：在 ReAct.py 中注册工具**

```python
from tools import ToolExecutor, search, calculate

calc_desc = "一个数学计算器，输入数学表达式（如 (123 + 456) * 789 / 12），返回计算结果。只支持 + - * / 和括号。"
tool_executor.registerTool("Calculate", calc_desc, calculate)
```

**运行流程：**

```
Question: 计算 (123 + 456) × 789 / 12 的结果？

第1步：
  Thought: 这是数学计算，使用 Calculate 工具
  Action: Calculate[(123 + 456) * 789 / 12]
  Observation: 38069.25

第2步：
  Thought: 已得到结果
  Action: Finish[结果是 38069.25]
```

注意：`×` 是中文乘号，LLM 会自动转成 `*` 再传给工具。

---

## 额外知识点

> 以下内容不属于本章节核心知识点，但在学习过程中涉及，供参考。

### E1: LLM 客户端类一般需要有什么接口和函数

> **知识类型**：通用概念 / 架构设计

一个标准的 LLM 客户端类通常需要以下接口和函数：

**核心接口**

```python
class LLMClient:
    def __init__(self, model: str, api_key: str, **kwargs): ...
    def chat(self, messages: list[dict], **kwargs) -> str: ...
    async def achat(self, messages: list[dict], **kwargs) -> str: ...
    def stream(self, messages: list[dict], **kwargs) -> Iterator[str]: ...
```

**工具调用支持（智能体必需）**

```python
    def chat_with_tools(self, messages, tools, **kwargs) -> dict: ...
```

**辅助函数**

```python
    def count_tokens(self, messages: list[dict]) -> int: ...
    def format_messages(self, role: str, content: str) -> dict: ...
```

关键设计点：
- `messages` 统一用 OpenAI 格式，方便多模型兼容
- 同步 + 异步双版本
- 工具调用单独一个方法，返回原始响应（需解析 `tool_calls`）
- 错误重试逻辑封装在这层

---

### E2: **kwargs 是什么意思

> **知识类型**：Python 基础语法

`**kwargs` 是 Python 的可变关键字参数，接收任意数量的 `key=value` 参数，在函数内部是一个普通字典。

```python
def chat(self, messages, **kwargs):
    params = {
        "model": self.model,
        "messages": messages,
        **kwargs  # 展开合并
    }

chat(messages, temperature=0.7, max_tokens=1000)
# kwargs = {"temperature": 0.7, "max_tokens": 1000}
```

| 语法 | 接收方式 | 示例 |
|------|---------|------|
| `*args` | 位置参数，存为元组 | `func(1, 2, 3)` |
| `**kwargs` | 关键字参数，存为字典 | `func(a=1, b=2)` |

LLM 客户端用它的原因：不同模型支持的参数不一样，用 `**kwargs` 可以灵活透传，不用每个参数都写死。

---

### E3: append() 函数

> **知识类型**：Python 基础语法

`append()` 是 Python 列表的内置方法，在列表末尾添加一个元素。

```python
history = []
history.append("Action: Search[华为手机]")
history.append("Observation: 华为Mate70是最新款")
# ["Action: Search[华为手机]", "Observation: 华为Mate70是最新款"]
```

| 方法 | 作用 |
|------|------|
| `append(x)` | 末尾加一个元素 |
| `extend([x, y])` | 末尾加多个元素 |
| `insert(i, x)` | 在指定位置插入 |
| `pop()` | 移除并返回最后一个元素 |

在 ReAct 里用 `append` 是因为每一步的 Action 和 Observation 都要按顺序追加，最后用 `"\n".join(self.history)` 拼成字符串传给 LLM。

---

### E4: dotenv 库

> **知识类型**：工具使用

`dotenv` 从 `.env` 文件加载环境变量，避免把密钥硬编码在代码里。

```bash
pip install python-dotenv
```

**.env 文件：**
```
ANTHROPIC_API_KEY=sk-ant-xxx
MODEL=claude-sonnet-4-6
```

**使用：**
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
model = os.getenv("MODEL", "claude-haiku-4-5-20251001")  # 第二个参数是默认值
```

核心规则：`.env` 加入 `.gitignore` 不提交到 git；`load_dotenv()` 只在本地开发用，生产环境由服务器直接注入环境变量。

---

### E5: .gitignore

> **知识类型**：工具使用

`.gitignore` 告诉 Git 哪些文件不需要追踪。

**Python 项目常见配置：**

```gitignore
# 环境变量（重要！密钥不能提交）
.env
.env.local

# Python 缓存
__pycache__/
*.pyc

# 虚拟环境
.venv/
venv/

# IDE
.vscode/
.idea/
```

关键点：已经被 Git 追踪的文件，加入 `.gitignore` 不会自动停止追踪，需要先运行：

```bash
git rm --cached <文件名>
```

---
