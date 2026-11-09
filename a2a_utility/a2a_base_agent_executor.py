import json

from a2a.helpers import (
    get_data_parts,
    get_message_text,
    new_data_part,
    new_task_from_user_message,
    new_text_message
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState

from agents.base_agent import BaseAgent

def create_agent_executor(agent: BaseAgent):
    return BaseAgentExecutor(agent)

class BaseAgentExecutor(AgentExecutor):
    def __init__(self, agent: BaseAgent):
        super().__init__()
        self.agent = agent
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        task = new_task_from_user_message(context.message)
        await event_queue.enqueue_event(task)

        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=task.id,
            context_id=task.context_id
        )
        data_parts = get_data_parts(context.message.parts)
        user_input = json.dumps(data_parts[0], ensure_ascii=False)
        print(user_input)
        content = await self.agent.run(user_input)
        await updater.add_artifact(
            parts=[new_data_part({"content": content}, media_type="application/json")]
        )
        await updater.update_status(
            state=TaskState.TASK_STATE_COMPLETED,
            message=new_text_message("Agent completed")
        )
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass
