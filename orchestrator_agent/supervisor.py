from .data_class import WorkflowState, Decision
class Supervisor:
    def __init__(self):
        pass
    async def decide(self, state: WorkflowState) -> Decision:
        if state["error"] is not None:
            return Decision("fail")
        
        if state["route_result"] is not None:
            return Decision("finish")

        if state["ops_snapshot"] is not None:
            return Decision("call_route")

        return Decision("call_ops")