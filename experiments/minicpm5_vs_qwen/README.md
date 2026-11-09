# MiniCPM5 2B 对比实验

测试日期：2026-11-08

## 模型

- MiniCPM5：`MiniCPM5-2B-Q4_K_M.gguf`
- 文件元数据实际参数规模：`2.6B`
- 对比模型：Youtu 2B、Qwen3.5 2B、Qwen3 1.7B

## 固定条件

- GPU：NVIDIA GeForce RTX 2050 4GB
- 后端：llama.cpp CUDA，build b12013
- GPU 全量卸载：`-ngl 99`
- 上下文：`-c 8192`
- 单并发：`-np 1`
- 关闭 reasoning：`-rea off --reasoning-budget 0`
- 统一基线采样：`temperature=0.1, top_p=0.95, top_k=50, repeat_penalty=1.1`
- MiniCPM5 推荐采样：`temperature=1.0, top_p=0.95, top_k=40, repeat_penalty=1.0`

## 测试集

复用 `../lfm3_vs_qwen3/benchmark.py`：

- 中文/英文精确输出
- 中文/英文数学
- 中文/英文 JSON 提取
- 中文/英文告警分类
- 中文/英文工具选择
- 中文/英文工具链
- 路径长度工具
- 较长上下文检索
- 网络概念问答

15 类用例 × 3 轮 = 45 次。

## MiniCPM5 两种采样对比

| 指标 | 统一基线 | MiniCPM5 推荐参数 |
|---|---:|---:|
| 任务正确率 | 75.6% | 80.0% |
| 严格格式遵循率 | 86.7% | 88.9% |
| 中位耗时 | 0.566s | 0.523s |
| P95 耗时 | 1.074s | 0.967s |
| 输出 token 中位数 | 23 | 23 |
| 截断次数 | 0 | 0 |

推荐参数略微更快，并提高了正确率和格式遵循率。

## 四模型横向对比

| 指标 | MiniCPM5 | Youtu 官方参数 | Qwen3.5 2B | Qwen3 1.7B |
|---|---:|---:|---:|---:|
| 正确率 | 80.0% | 86.7% | 100.0% | 100.0% |
| 严格格式遵循率 | 88.9% | 97.8% | 93.3% | 86.7% |
| 中位耗时 | 0.523s | 0.566s | 1.323s | 1.130s |
| P95 耗时 | 0.967s | 0.959s | 2.784s | 2.041s |
| 输出 token 中位数 | 23 | 22 | 32 | 27 |

MiniCPM5 与 Youtu 的延迟非常接近，P95 基本持平。Youtu 在正确率和格式
遵循率上更好，因此快速模型里 Youtu 的综合表现更稳。

## 实际 Agent 端到端

MiniCPM5 推荐参数：

| 轮次 | BFS | 路径智能体 | 端到端 |
|---|---:|---:|---:|
| 1 | 1.272s | 1.027s | 2.361s |
| 2 | 1.002s | 0.773s | 1.847s |
| 3 | 1.029s | 0.751s | 1.854s |

预热后中位约 `1.85s`。

| 模型 | Agent 端到端中位数 |
|---|---:|
| MiniCPM5 2B | 1.85s |
| Youtu 2B | 1.88s |
| Qwen3 1.7B | 3.28s |
| Qwen3.5 2B | 4.76s |

## 失败样本

MiniCPM5 推荐参数下：

- 中文 JSON 仅 1/3 正确，模型会用 Markdown 代码块包裹 JSON；
- 英文 JSON 2/3 正确，有一轮把 device 输成 `"Device"`、interface 输成 `"R2"`；
- 中文分类 0/3 正确，输出了中文“链路”，而不是契约标签 `LINK`；
- 中文路径长度 0/3 严格格式正确，工具调用和结果 `3` 都正确，但最终输出为
  “路径 A → B → D → G 的长度为 3。”而不是纯整数。

## 结论

- 固定 BFS/路径 Agent 的低延迟场景：MiniCPM5 和 Youtu 都属于 1.8–1.9 秒级。
- Youtu 综合更稳：速度相近，但正确率和格式遵循率更高。
- MiniCPM5 不建议单独承担 JSON、分类、严格输出协议等任务。
- 需要高正确率时仍应使用 Qwen3 1.7B 或 Qwen3.5 2B。

## 原始数据

- `minicpm5_2b_results.json`
- `minicpm5_2b_official_results.json`
