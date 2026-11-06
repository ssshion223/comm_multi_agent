from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill
)

def create_agent_card(
    name: str,
    description: str,
    url: str,
    skills: list[AgentSkill],
    version: str="1.0.0",
    protocol_binding: str="JSONRPC",
    protocol_version: str="1.0",
    input_modes: list[str]=["application/json"],
    output_modes: list[str]=["application/json"],
    streaming: bool=False
) -> AgentCard:
    return AgentCard(
        name=name,
        description=description,
        version=version,
        default_input_modes=input_modes,
        default_output_modes=output_modes,
        capabilities=AgentCapabilities(streaming=streaming),
        supported_interfaces=[
            AgentInterface(
                protocol_binding=protocol_binding,
                url=url,
                protocol_version=protocol_version,
            )
        ],
        skills=skills
    )