from langgraph.graph import END, START, StateGraph

from .data_class import WorkflowState
from .supervisor import Supervisor
from .worker_gateway import WorkerGateway


class WorkflowManager:
    def __init__(self, supervisor: Supervisor, gateway: WorkerGateway):
        self.supervisor = supervisor
        self.gateway = gateway
        self.graph = None

    def start(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(WorkflowState)

        builder.add_node("supervisor", self._supervisor_node)
        builder.add_node("ops_node", self._ops_node)
        builder.add_node("route_node", self._route_node)

        builder.add_edge(START, "supervisor")
        builder.add_conditional_edges(
            "supervisor",
            lambda state: state["action"],
            {
                "call_ops": "ops_node",
                "call_route": "route_node",
                "finish": END,
                "fail": END,
            },
        )
        builder.add_edge("ops_node", "supervisor")
        builder.add_edge("route_node", "supervisor")

        return builder.compile()

    async def _supervisor_node(self, state: WorkflowState):
        decision = await self.supervisor.decide(state)
        return {"action": decision.action}

    async def _ops_node(self, state: WorkflowState):
        try:
            snapshot = await self.gateway.get_ops_snapshot()
            return {"ops_snapshot": snapshot}
        except Exception as error:
            return {"error": str(error)}

    async def _route_node(self, state: WorkflowState):
        try:
            result = await self.gateway.plan_routes(state["ops_snapshot"])
            return {"route_result": result}
        except Exception as error:
            return {"error": str(error)}

    async def run(self):
        return await self.graph.ainvoke({
            "ops_snapshot": None,
            "route_result": None,
            "error": None,
        })
