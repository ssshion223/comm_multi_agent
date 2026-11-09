import asyncio
import time
from a2a_utility import create_agent_client

async def main():
    total_start = time.perf_counter()
    bfs_agent_client = create_agent_client("http://127.0.0.1:9001")
    path_agent_client = create_agent_client("http://127.0.0.1:9002")
    connect_start = time.perf_counter()
    await bfs_agent_client.connect()
    await path_agent_client.connect()
    connect_elapsed = time.perf_counter() - connect_start
    try:
        bfs_start = time.perf_counter()
        result1 = await bfs_agent_client.call("Find the shortest path from A to G")
        bfs_elapsed = time.perf_counter() - bfs_start
        path_start = time.perf_counter()
        result2 = await path_agent_client.call(f"Calculate the length of this path: {result1}")
        path_elapsed = time.perf_counter() - path_start
        print(result1)
        print(result2)
        print(f"connect: {connect_elapsed:.3f}s")
        print(f"bfs_agent: {bfs_elapsed:.3f}s")
        print(f"path_agent: {path_elapsed:.3f}s")
        print(f"total: {time.perf_counter() - total_start:.3f}s")
    finally:
        await bfs_agent_client.close()
        await path_agent_client.close()
        
if __name__ == "__main__":
    asyncio.run(main())
