import asyncio
from a2a_utility import create_agent_client

async def main():
    bfs_agent_client = create_agent_client("http://127.0.0.1:9001")
    path_agent_client = create_agent_client("http://127.0.0.1:9002")
    await bfs_agent_client.connect()
    await path_agent_client.connect()
    try:
        result1 = await bfs_agent_client.call({"input": "A到G的路径"})
        result2 = await path_agent_client.call({"input": f"计算这个路径的长度:{result1}"})
        print(result1)
        print(result2)
    finally:
        await bfs_agent_client.close()
        await path_agent_client.close()
        
if __name__ == "__main__":
    asyncio.run(main())