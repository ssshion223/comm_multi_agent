import asyncio


class Orchestrator:
    def __init__(self, agent1_client, agent2_client):
        self.agent1_client = agent1_client
        self.agent2_client = agent2_client

    async def run(self, start, end):
        agent1_result = await self.agent1_client.send({
            "start": start,
            "end": end
        })

        return await self.agent2_client.send({
            "path": agent1_result["path"]
        })