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
        system_prompt="回答简洁完整，你是bfs智能体",
        tools=[BFS_TOOL],
        tool_functions={"bfs_search": bfs_search}
    )

def create_path_agent() -> BaseAgent:
    return BaseAgent(
        name="path agent",
        client=llm_client,
        model=llm_model,
        system_prompt="回答简洁完整，你是计算路径长度的智能体",
        tools=[CAL_PATH_LEN_TOOL],
        tool_functions={"cal_path_len": cal_path_len}
    )