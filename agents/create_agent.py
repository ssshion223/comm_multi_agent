from agents.base_agent import BaseAgent
from config.configuration import llm_model
from tools import (
    BFS_TOOL, bfs_search,
    CAL_PATH_LEN_TOOL, cal_path_len
    )
from llm.client import llm_client

def create_bfs_agent() -> BaseAgent:
    return BaseAgent(
        name="bfs_agent",
        client=llm_client,
        model=llm_model,
        system_prompt=(
            "You must call bfs_search(start, end) first. "
            "Do not output any text before the tool returns. "
            "After the tool returns, output only the shortest path, "
            "joining node names with →. Do not explain and do not output JSON."
        ),
        tools=[BFS_TOOL],
        tool_functions={"bfs_search": bfs_search}
    )

def create_path_agent() -> BaseAgent:
    return BaseAgent(
        name="path agent",
        client=llm_client,
        model=llm_model,
        system_prompt=(
            "Calling cal_path_len is the only way to calculate the path length. "
            "Extract the path node list from the input and call cal_path_len(path) first. "
            "Do not give a length before the tool returns. "
            "After the tool returns, output only the integer itself. "
            "Do not explain, output JSON, Markdown, units, or punctuation."
        ),
        tools=[CAL_PATH_LEN_TOOL],
        tool_functions={"cal_path_len": cal_path_len}
    )
