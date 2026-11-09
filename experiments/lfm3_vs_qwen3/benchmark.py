import argparse
import asyncio
import json
import math
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tools import BFS_TOOL, CAL_PATH_LEN_TOOL, bfs_search, cal_path_len


@dataclass
class Case:
    case_id: str
    category: str
    system: str
    prompt: str
    check: str
    expected: Any
    tool: dict | None = None
    tool_function: Any = None
    tool_result_mode: str | None = None


@dataclass
class SamplingConfig:
    temperature: float = 0.1
    top_p: float = 0.95
    top_k: int = 50
    repeat_penalty: float | None = 1.1

    def extra_body(self) -> dict:
        body = {"top_k": self.top_k}
        if self.repeat_penalty is not None:
            body["repeat_penalty"] = self.repeat_penalty
        return body


def normalize(text: str | None) -> str:
    return (text or "").strip().strip("`").strip()


def compile_long_context() -> str:
    lines = [
        f"Line {index}: unrelated network telemetry record {index}."
        for index in range(1, 121)
    ]
    lines.insert(67, "The secret maintenance code is BLUE-42.")
    return "\n".join(lines)


LONG_CONTEXT = compile_long_context()

CASES = [
    Case(
        "zh_exact_ok",
        "instruction_zh",
        "严格遵守格式要求。",
        "只输出两个字：正常",
        "exact",
        "正常",
    ),
    Case(
        "en_exact_ok",
        "instruction_en",
        "Follow the output format exactly.",
        "Output exactly this word: OK",
        "exact",
        "OK",
    ),
    Case(
        "zh_math",
        "reasoning_zh",
        "只输出最终答案，不要解释。",
        "4 加 3 等于多少？只输出阿拉伯数字。",
        "exact",
        "7",
    ),
    Case(
        "en_math",
        "reasoning_en",
        "Output only the final answer. Do not explain.",
        "What is 4 plus 5? Output only the Arabic numeral.",
        "exact",
        "9",
    ),
    Case(
        "zh_json",
        "json_zh",
        "只输出合法 JSON，不要 Markdown。",
        (
            "从文本提取 JSON，字段为 device、interface、status："
            "设备 R1 的接口 Gi0/1 当前状态为 DOWN。"
        ),
        "json",
        {"device": "R1", "interface": "Gi0/1", "status": "DOWN"},
    ),
    Case(
        "en_json",
        "json_en",
        "Return valid JSON only. Do not use Markdown.",
        (
            "Extract JSON with fields device, interface, status from: "
            "Device R2 interface Gi0/2 is DOWN."
        ),
        "json",
        {"device": "R2", "interface": "Gi0/2", "status": "DOWN"},
    ),
    Case(
        "zh_classify",
        "classification_zh",
        "只输出标签，不要解释。",
        "将告警分类为 LINK 或 DEVICE，只输出标签：链路 R1-R2 丢包率从 0% 升到 20%。",
        "exact",
        "LINK",
    ),
    Case(
        "en_classify",
        "classification_en",
        "Output only the label. Do not explain.",
        (
            "Classify the alert as LINK or DEVICE. Output only the label: "
            "Packet loss on link R1-R2 increased from 0% to 20%."
        ),
        "exact",
        "LINK",
    ),
    Case(
        "zh_tool_select",
        "tool_select_zh",
        "用户询问路径时必须调用 bfs_search。",
        "查询 C 到 D 的最短路径。",
        "tool",
        {"name": "bfs_search", "arguments": {"start": "C", "end": "D"}},
        tool=BFS_TOOL,
        tool_function=bfs_search,
    ),
    Case(
        "en_tool_select",
        "tool_select_en",
        "You must call bfs_search when the user asks for a path.",
        "Find the shortest path from C to D.",
        "tool",
        {"name": "bfs_search", "arguments": {"start": "C", "end": "D"}},
        tool=BFS_TOOL,
        tool_function=bfs_search,
    ),
    Case(
        "zh_tool_chain",
        "tool_chain_zh",
        (
            "必须先调用 bfs_search。工具返回后只输出路径节点，用 → 连接，"
            "不要解释。"
        ),
        "查询 A 到 G 的最短路径。",
        "tool_chain",
        {"path": ["A", "B", "D", "G"], "compact_path": "A→B→D→G"},
        tool=BFS_TOOL,
        tool_function=bfs_search,
        tool_result_mode="bfs",
    ),
    Case(
        "en_tool_chain",
        "tool_chain_en",
        (
            "You must call bfs_search first. After the tool returns, output only "
            "the path nodes joined by →. Do not explain."
        ),
        "Find the shortest path from A to G.",
        "tool_chain",
        {"path": ["A", "B", "D", "G"], "compact_path": "A→B→D→G"},
        tool=BFS_TOOL,
        tool_function=bfs_search,
        tool_result_mode="bfs",
    ),
    Case(
        "zh_path_length",
        "path_length_zh",
        (
            "必须调用 cal_path_len(path)。工具返回后只输出整数本身，"
            "不要解释或输出 JSON。"
        ),
        "计算路径 A → B → D → G 的长度。",
        "path_length",
        3,
        tool=CAL_PATH_LEN_TOOL,
        tool_function=cal_path_len,
        tool_result_mode="path_length",
    ),
    Case(
        "long_context",
        "long_context",
        "Answer with the exact code only.",
        (
            "Find the secret maintenance code in the following text and reply "
            f"with the code only:\n{LONG_CONTEXT}"
        ),
        "exact",
        "BLUE-42",
    ),
    Case(
        "network_concept",
        "network_knowledge",
        "用一句中文回答，包含“丢包”和“时延”两个词。",
        "网络链路丢包和时延的核心区别是什么？",
        "contains_all",
        ["丢包", "时延"],
    ),
]


def check_text(case: Case, content: str | None) -> tuple[bool, bool]:
    text = normalize(content)
    if case.check == "exact":
        return text.casefold() == str(case.expected).casefold(), True
    if case.check == "json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return False, False
        return parsed == case.expected, True
    if case.check == "contains_all":
        return all(word in text for word in case.expected), True
    return False, False


def compact_path(text: str) -> str:
    return re.sub(r"\s+", "", text).strip("。.!`")


def check_tool_chain(case: Case, content: str | None, path: list[str]) -> tuple[bool, bool]:
    text = normalize(content)
    if case.check == "tool_chain":
        expected = case.expected
        correct_path = path == expected["path"]
        exact = compact_path(text) == expected["compact_path"]
        return correct_path, exact
    if case.check == "path_length":
        exact = text == str(case.expected)
        return exact, exact
    return False, False


async def call_model(
    client: AsyncOpenAI,
    messages: list[dict],
    tools: list[dict] | None,
    sampling: SamplingConfig,
    max_tokens: int = 256,
) -> tuple[Any, float]:
    started = time.perf_counter()
    response = await client.chat.completions.create(
        model="local",
        messages=messages,
        tools=tools or None,
        max_tokens=max_tokens,
        temperature=sampling.temperature,
        top_p=sampling.top_p,
        extra_body=sampling.extra_body(),
    )
    return response, time.perf_counter() - started


def extract_metrics(response: Any, elapsed: float) -> dict:
    usage = response.usage
    timings = response.timings or {}
    return {
        "wall_seconds": elapsed,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "finish_reason": response.choices[0].finish_reason,
        "decode_tokens_per_second": timings.get("predicted_per_second"),
        "prompt_tokens_per_second": timings.get("prompt_per_second"),
    }


async def run_case(
    client: AsyncOpenAI, case: Case, sampling: SamplingConfig
) -> dict:
    messages = [
        {"role": "system", "content": case.system},
        {"role": "user", "content": case.prompt},
    ]

    if case.tool is None:
        response, elapsed = await call_model(client, messages, None, sampling)
        content = response.choices[0].message.content
        passed, format_ok = check_text(case, content)
        result = extract_metrics(response, elapsed)
        result.update(
            {
                "case_id": case.case_id,
                "category": case.category,
                "passed": passed,
                "format_ok": format_ok,
                "content": content,
            }
        )
        return result

    first, first_elapsed = await call_model(
        client, messages, [case.tool], sampling
    )
    first_message = first.choices[0].message
    tool_calls = first_message.tool_calls or []
    tool_ok = False
    selected: dict[str, Any] = {}
    tool_result = None

    if tool_calls:
        tool_call = tool_calls[0]
        try:
            arguments = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            arguments = {}
        selected = {"name": tool_call.function.name, "arguments": arguments}
        tool_ok = selected == case.expected if case.check == "tool" else (
            selected["name"] == case.tool["function"]["name"]
        )
        if tool_ok and case.tool_function is not None:
            tool_result = case.tool_function(**arguments)

    totals = extract_metrics(first, first_elapsed)
    totals.update(
        {
            "case_id": case.case_id,
            "category": case.category,
            "tool_called": bool(tool_calls),
            "tool_ok": tool_ok,
            "tool_selected": selected,
            "tool_result": tool_result,
        }
    )

    if case.check == "tool":
        totals["passed"] = tool_ok
        totals["format_ok"] = tool_ok
        return totals

    second = None
    second_elapsed = 0.0
    content = None
    if tool_calls and tool_ok:
        messages.append(first_message)
        for index, tool_call in enumerate(tool_calls):
            arguments = json.loads(tool_call.function.arguments)
            result = case.tool_function(**arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
            if index == 0:
                tool_result = result
        second, second_elapsed = await call_model(
            client, messages, [case.tool], sampling
        )
        content = second.choices[0].message.content
        second_metrics = extract_metrics(second, second_elapsed)
        totals["completion_tokens"] += second_metrics["completion_tokens"]
        totals["prompt_tokens"] += second_metrics["prompt_tokens"]
        totals["wall_seconds"] += second_metrics["wall_seconds"]
        totals["finish_reason"] = second_metrics["finish_reason"]
        if second_metrics["decode_tokens_per_second"]:
            totals["decode_tokens_per_second"] = second_metrics[
                "decode_tokens_per_second"
            ]

    path = tool_result.get("path", []) if isinstance(tool_result, dict) else []
    passed, format_ok = check_tool_chain(case, content, path)
    totals.update(
        {
            "passed": passed and tool_ok,
            "format_ok": format_ok and tool_ok,
            "tool_result": tool_result,
            "content": content,
        }
    )
    return totals


async def warmup(client: AsyncOpenAI, sampling: SamplingConfig) -> None:
    await call_model(
        client,
        [{"role": "user", "content": "Reply with OK only."}],
        None,
        sampling,
        max_tokens=16,
    )


def percentile(values: list[float], p: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    rank = (len(ordered) - 1) * p
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


def summarize(label: str, runs: list[dict]) -> dict:
    by_case: dict[str, list[dict]] = {}
    for row in runs:
        by_case.setdefault(row["case_id"], []).append(row)

    case_summary = []
    for case_id, rows in by_case.items():
        case_summary.append(
            {
                "case_id": case_id,
                "category": rows[0]["category"],
                "runs": len(rows),
                "pass_rate": sum(row["passed"] for row in rows) / len(rows),
                "format_rate": sum(row["format_ok"] for row in rows) / len(rows),
                "median_seconds": percentile(
                    [row["wall_seconds"] for row in rows], 0.5
                ),
                "median_completion_tokens": percentile(
                    [row["completion_tokens"] for row in rows], 0.5
                ),
                "median_decode_tps": percentile(
                    [
                        row["decode_tokens_per_second"]
                        for row in rows
                        if row["decode_tokens_per_second"]
                    ],
                    0.5,
                ),
                "truncated_runs": sum(
                    row["finish_reason"] == "length" for row in rows
                ),
            }
        )

    total_runs = len(runs)
    return {
        "label": label,
        "total_runs": total_runs,
        "overall_pass_rate": sum(row["passed"] for row in runs) / total_runs,
        "overall_format_rate": sum(row["format_ok"] for row in runs)
        / total_runs,
        "overall_median_seconds": percentile(
            [row["wall_seconds"] for row in runs], 0.5
        ),
        "overall_p95_seconds": percentile(
            [row["wall_seconds"] for row in runs], 0.95
        ),
        "overall_median_completion_tokens": percentile(
            [row["completion_tokens"] for row in runs], 0.5
        ),
        "truncated_runs": sum(row["finish_reason"] == "length" for row in runs),
        "cases": case_summary,
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--output", required=True)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument(
        "--repeat-penalty",
        type=float,
        default=1.1,
        help="Set to 0 to omit repeat_penalty from the request.",
    )
    args = parser.parse_args()

    sampling = SamplingConfig(
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        repeat_penalty=args.repeat_penalty or None,
    )
    client = AsyncOpenAI(base_url=args.base_url, api_key="local")
    await warmup(client, sampling)

    runs = []
    for run_index in range(args.runs):
        for case in CASES:
            row = await run_case(client, case, sampling)
            row["run_index"] = run_index + 1
            runs.append(row)
            print(
                f"{args.label} run={run_index + 1} "
                f"case={case.case_id} pass={row['passed']} "
                f"format={row['format_ok']} "
                f"seconds={row['wall_seconds']:.3f} "
                f"tokens={row['completion_tokens']}",
                flush=True,
            )

    result = {
        "label": args.label,
        "base_url": args.base_url,
        "runs_per_case": args.runs,
        "sampling": {
            "temperature": sampling.temperature,
            "top_p": sampling.top_p,
            "top_k": sampling.top_k,
            "repeat_penalty": sampling.repeat_penalty,
        },
        "summary": summarize(args.label, runs),
        "rows": runs,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
