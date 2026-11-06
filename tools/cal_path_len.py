

def cal_path_len(path):
    return len(path) - 1


CAL_PATH_LEN_TOOL = {
    "type": "function",
    "function": {
        "name": "cal_path_len",
        "description": (
            "计算路径长度，即路径包含的边数。"
            "当已有从起点到终点按顺序排列的节点列表并需要报告跳数时使用。"
            "返回 path 中相邻节点之间的边数，等于 len(path) - 1；单节点路径返回 0。"
            "path 应至少包含一个节点。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "array",
                    "description": "从起点到终点按顺序排列的节点名称列表",
                    "items": {
                        "type": "string",
                        "description": "单个路径节点名称，例如 A、B 或 G",
                    },
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
}


if __name__ == "__main__":
    print(cal_path_len(["C", "F", "G"]))

