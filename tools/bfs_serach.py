from collections import deque


GRAPH = {
    "A": ["B", "C"],
    "B": ["A", "D", "E"],
    "C": ["A", "F"],
    "D": ["B", "G"],
    "E": ["B", "G"],
    "F": ["C", "G"],
    "G": ["D", "E", "F"],
}


def bfs_search(start: str = "C", end: str = "D") -> dict:
    if start not in GRAPH or end not in GRAPH:
        return {"found": False, "path": []}

    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        node, path = queue.popleft()

        if node == end:
            return {"found": True, "path": path}

        for neighbor in GRAPH.get(node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return {"found": False, "path": []}




BFS_TOOL = {
    "type": "function",
    "function": {
        "name": "bfs_search",
        "description": (
            "在固定的邻接图中查找两个节点之间的最短路径。"
            "当用户询问路径、可达性或最少跳数时使用。"
            "start 和 end 必须是 GRAPH 中已有的节点。"
            "返回 found 表示是否可达，path 表示完整路径。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start": {
                    "type": "string",
                    "description": "起始节点名称，例如 A",
                },
                "end": {
                    "type": "string",
                    "description": "目标节点名称，例如 G",
                },
            },
            "required": ["start", "end"],
            "additionalProperties": False,
        },
    },
}


if __name__ == "__main__":
    print(bfs_search())
