from openai import AsyncOpenAI
from config.configuration import llm_api_key, llm_url

llm_client = AsyncOpenAI(
    base_url=llm_url,
    api_key=llm_api_key
)