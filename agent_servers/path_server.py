from agents import create_path_agent
from a2a_utility import (
    create_agent_executor,
    create_agent_card,
    create_agent_server
    )
from a2a.types import AgentSkill

host = "127.0.0.1"
port = 9002

agent = create_path_agent()
agent_executor = create_agent_executor(agent=agent)
agent_card = create_agent_card(
    name="path_agent",
    description="sui bian xie de",
    url=f"http://{host}:{port}/",
    skills=[
        AgentSkill(
            id="path calculate",
            name="path cal",
            description="sui bian xie de",
            tags=["path", "calculate"],
            input_modes=["application/json"],
            output_modes=["application/json"],
            examples=['{"path": ["C", "F", "G"]}']
        )
    ]
)

agent_server = create_agent_server(
    agent_executor=agent_executor,
    agent_card=agent_card,
    host=host,
    port=port
    )

if __name__ == "__main__":
    agent_server.run()