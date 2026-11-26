import asyncio
from typing import Any
from ops_agent.body import OpsAgent
from route_agent.body import RouteAgent
class WorkerGateway:
    def __init__(self, ops_agent: OpsAgent, route_agent: RouteAgent):
        self.ops_agent = ops_agent
        self.route_agent = route_agent

    async def get_ops_snapshot(self):
        await asyncio.to_thread(self.ops_agent.start)
        return self.ops_agent

    async def plan_routes(self, ops_snapshot):
        return await asyncio.to_thread(
            self.route_agent.start,
            ops_snapshot
        )