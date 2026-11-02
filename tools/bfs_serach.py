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


def bfs_serach(start: str = "C", end: str = "D") -> dict:
    if start not in GRAPH or end not in GRAPH:
        return {"found": False, "path": []}

    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        node, path = queue.popleft()

        if node == end:
            return {"found": True, "path": path}

        for neighbor in GRAPH.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return {"found": False, "path": []}


bfs_search = bfs_serach


if __name__ == "__main__":
    print(bfs_serach())
