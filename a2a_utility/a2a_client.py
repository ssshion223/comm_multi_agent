
from a2a.client import ClientConfig, ClientCallContext, create_client
from a2a.helpers import get_data_parts, new_data_message
from a2a.types import Role, SendMessageRequest

class AgentClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.client = None

    async def connect (self):
        self.client = await create_client(
            agent=self.base_url,
            client_config=ClientConfig(streaming=False)
        )

    async def call(self, data: dict, timeout: float = 120) -> dict:
        request = SendMessageRequest(
            message=new_data_message(
                data=data,
                media_type="application/json",
                role=Role.ROLE_USER
            )
        )
        context = ClientCallContext(timeout=timeout)
        async for event in self.client.send_message(request, context=context):
            if event.HasField("task"):
                return self._extract_task_data(event.task)

    def _extract_task_data(self, task):
        for artifact in task.artifacts:
            data_parts = get_data_parts(artifact.parts)
            if data_parts:
                return data_parts[-1]
        return None
    async def close(self):
        await self.client.close()

def create_agent_client(base_url: str) -> AgentClient:
    return AgentClient(base_url)