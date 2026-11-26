from ops_agent.body import OpsAgent
from route_agent.body import RouteAgent

from .supervisor import Supervisor
from .worker_gateway import WorkerGateway
from .workflow_manager import WorkflowManager


class OrchestratorAgent:
    def __init__(self, ops_agent: OpsAgent, route_agent: RouteAgent):
        self.supervisor = Supervisor()
        self.gateway = WorkerGateway(ops_agent, route_agent)
        self.workflow_manager = WorkflowManager(
            supervisor=self.supervisor,
            gateway=self.gateway,
        )

    def start(self):
        self.workflow_manager.start()

    async def run(self):
        return await self.workflow_manager.run()
