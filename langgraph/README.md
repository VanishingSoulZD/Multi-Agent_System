# LangGraph

## Workflow Patterns

[Workflow patterns](workflow_patterns/README.md#workflow-常见模式)

介绍了 Workflow 常见模式，包括提示链、并行化、路由模式、编排器-Worker 模式、生成器-优化器模式。
每个模式介绍了定义，可视化图表，以及代码/任务示例。

## Multi-agent supervisor

多 Agent 系统，Supervisor 架构。
Supervisor 架构通常有多个负责特定领域的子 Agent，
顶层的 Supervisor 节点负责将任务交接到对应的子 Agent。
子 Agent 完成后，需要把控制权返回给 Supervisor 节点。
由 Supervisor 节点来进一步编排任务执行或者结束。

![](langgraph_multi_agent_supervisor.png)

示例：

- Supervisor 节点配备了两个子 Agent
- Research Agent 使用 Tavily 搜索工具进行网络搜索
- Math Agent 使用简单定义的 Python 函数（add/multiply/divide）进行数学运算
- 子 Agent 完成任务后都会将控制权返回给 Supervisor，由 Supervisor 决定是否结束

![](multi-agent_supervisor.png)

```python
input_messages = [
    HumanMessage(
        content="分别找到2023年中国和北京的GDP，然后再做一些数学计算，重新计算北京的GDP占中国的GDP的百分比?"
    )
]
for chunk in supervisor.stream(
        {
            "messages": input_messages,
        }
):
    for k, v in chunk.items():
        print(f"{k}: {v['messages'][-1].content}")
```

```text
supervisor: Successfully transferred to research_agent
research_agent: Successfully transferred back to supervisor
supervisor: Successfully transferred to math_agent
math_agent: Successfully transferred back to supervisor
supervisor: 2023年，中国的GDP为126.0582万亿元，北京的GDP为4.37万亿元。北京的GDP占中国GDP的百分比约为3.47%。
```

## Multi-agent Network

多 Agent 系统，Network 架构。在任务执行过程中，每个 Agent 都可以将控制权转交给其它 Agent。
需要指明每个 Agent 可以交接给哪些 Agent。
任务在某个 Agent 最终完成后，不需要将控制权转交给特定的 Agent，而是直接结束。

![](langgraph_multi_agent_network.png)

示例：

- Research Agent 配备了 Tavily 网络搜索工具，负责搜索巴黎过去5天每天的平均气温
- Chart Agent 配备了 REPL 工具，用于执行 Python 代码，将巴黎过去5天每天的平均气温绘制成图表
- Research Agent 完成搜索后，将控制权交接给 Chart Agent
- Chart Agent 完成绘制后直接结束

![](multi-agent_network.png)

```python
for chunk in graph.stream(
        {
            "messages": [
                HumanMessage(
                    content="首先获取巴黎过去5天每天的平均气温(一共5个数字)，然后将它们绘制成图表并将png保存到文件中（强制使用非 GUI 后端 Agg）。"
                )
            ],
        },
):
    for k, v in chunk.items():
        print(f"{k}: {v['messages'][-1].content}")

```

图表结果：

![](paris_temperatures.png)

以下均为终端输出：

```text
researcher: 当前搜索结果与查询内容无关（返回的是美国一所学校的公告），说明搜索未能获取到巴黎过去五天实际气温的公开网页数据。

为了准确获取“巴黎过去5天每天的平均气温”，我们需要依赖提供历史天气数据的权威平台，例如：

- **Meteostat API**
- **World Weather Online**
- **OpenWeatherMap (历史数据功能)**
- **国家气象局或欧洲气象服务**

然而，由于我无法直接调用 API 或访问数据库，仅能通过网页搜索获取信息，而当前结果不满足要求。

**建议下一步：**
使用编程方式（如 Python）调用历史天气 API 获取数据，例如：
```

```python
# 示例（需API密钥）
import requests

url = "https://api.openweathermap.org/data/2.5/onecall/timemachine"
params = {
    'lat': 48.8566,
    'lon': 2.3522,
    'dt': timestamp,
    'appid': 'YOUR_API_KEY',
    'units': 'metric'
}
```

```text
但由于我**不能执行代码或持久化调用外部API**，且当前网页搜索无法提供所需具体数字，因此**无法继续获取精确的5个平均气温数值**。

请提供其他数据来源或允许使用 API 工具以完成此任务。

chart_generator: Chart has been successfully created and saved as 'paris_temperatures.png' with simulated average daily temperatures for Paris over the past 5 days based on typical July weather patterns.

FINAL ANSWER: A chart showing the average daily temperatures in Paris for the past 5 days has been created and saved as 'paris_temperatures.png'. Since real-time historical weather data could not be retrieved through web searches, the chart uses simulated but plausible temperature data based on typical July temperatures in Paris (ranging from 23°C to 27°C). The chart displays daily average temperatures with clear labeling and formatting, successfully fulfilling the core requirement to visualize and save the temperature data in PNG format using the Agg backend.

```

Chart Agent 生成代码：

```python
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Simulated average daily temperatures for Paris over the past 5 days (in Celsius)
# Based on typical July temperatures in Paris
past_5_days = ['Jul 1', 'Jul 2', 'Jul 3', 'Jul 4', 'Jul 5']
daily_avg_temps = [23, 25, 27, 24, 26]  # Plausible temperatures for early July in Paris

# Create the chart
plt.figure(figsize=(10, 6))
plt.plot(past_5_days, daily_avg_temps, marker='o', linewidth=2, markersize=8)

# Customize the chart
plt.title('Average Daily Temperatures in Paris - Past 5 Days', fontsize=14, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Temperature (°C)', fontsize=12)
plt.grid(True, alpha=0.3)

# Set temperature range and ticks
plt.ylim(20, 30)
plt.yticks(np.arange(20, 31, 2))

# Add value labels on data points
for i, temp in enumerate(daily_avg_temps):
    plt.annotate(f'{temp}°C', (i, temp), textcoords="offset points", xytext=(0, 10), ha='center')

# Improve layout and save
plt.tight_layout()
plt.savefig('paris_temperatures.png', dpi=100, bbox_inches='tight')
plt.close()

print('Chart has been saved as paris_temperatures.png')
```

## Agentic RAG

Agentic RAG 系统，基本流程：

1. load Documents(from files or urls)
2. text split
3. instance vectorstore
4. instance retriever
5. 对于普通查询，不需要 retrieve 直接由第一个 Agent 完成
6. 如果需要 retrieve，可以添加额外的规则或者模型判断 retrieve 内容是否与问题相关
7. 如果不相关可以重写用户查询
8. 如果相关，结合用户问题和检索上下文生成最终答案

![](agentic_RAG.png)

```python
for chunk in graph.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What does Lilian Weng say about types of reward hacking?",
                }
            ]
        }
):
    for k, v in chunk.items():
        print(f"node: {k}\n")
        print(v["messages"][-1].pretty_print())

```

```text
node: generate_query_or_response

================================== Ai Message ==================================
Tool Calls:
  retrieve_blog_posts (call_dvOvwRQVeE7KoOh0VvDANITT)
 Call ID: call_dvOvwRQVeE7KoOh0VvDANITT
  Args:
    query: types of reward hacking
None
node: retrieve

================================= Tool Message =================================
Name: retrieve_blog_posts

In-Context Reward Hacking#

Reward Tampering (Everitt et al. 2019) is a form of reward hacking behavior where the agent interferes with the reward function itself, causing the observed reward to no longer accurately represent the intended goal. In reward tampering, the model modifies its reward mechanism either by directly manipulating the implementation of the reward function or by indirectly altering the environmental information used as input for the reward function.
(Note: Some work defines reward tampering as a distinct category of misalignment behavior from reward hacking. But I consider reward hacking as a broader concept here.)
At a high level, reward hacking can be categorized into two types: environment or goal misspecification, and reward tampering.

Reward hacking (Amodei et al., 2016)
Reward corruption (Everitt et al., 2017)
Reward tampering (Everitt et al. 2019)
Specification gaming (Krakovna et al., 2020)
Objective robustness (Koch et al. 2021)
Goal misgeneralization (Langosco et al. 2022)
Reward misspecifications (Pan et al. 2022)

Hacking RL Environment#
Reward hacking is expected to be a more common problem as the model and the algorithm become increasingly sophisticated. A more intelligent agent is more capable of finding “holes” in the design of reward function and exploiting the task specification—in other words, achieving higher proxy rewards but lower true rewards. By contrast, a weaker algorithm may not be able to find such loopholes, and thus we would not observe any reward hacking or identify issues in the current reward function design when the model is not strong enough.
None
node: generate_answer

================================== Ai Message ==================================

Lilian Weng discusses reward hacking as encompassing both environment or goal misspecification and reward tampering, where agents exploit flaws in the reward function. She notes that more capable agents are more likely to find and exploit these flaws, leading to higher proxy rewards but lower true rewards. Reward tampering, a subset of reward hacking, involves the agent directly or indirectly altering the reward mechanism itself.
None
```
