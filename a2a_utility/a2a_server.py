import uvicorn
from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from starlette.applications import Starlette

class AgentServer:
    def __init__(self,
                 agent_executor: AgentExecutor,
                 agent_card: AgentCard,
                 host: str,
                 port: int):
        handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
            agent_card=agent_card
        )
        routes = [
            *create_agent_card_routes(agent_card),
            *create_jsonrpc_routes(handler, "/")
        ]
        self.app = Starlette(routes=routes)
        self.host = host
        self.port = port
    def run(self):
        uvicorn.run(self.app,
                    host=self.host,
                    port=self.port)

def create_agent_server(agent_executor: AgentExecutor,
                      agent_card: AgentCard,
                      host: str,
                      port: int):
    return AgentServer(agent_executor=agent_executor,
                       agent_card=agent_card,
                       host=host,
                       port=port)



