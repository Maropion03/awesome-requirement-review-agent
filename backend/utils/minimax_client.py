import os
from typing import Optional

from langchain_openai import ChatOpenAI


def get_minimax_client(
    model: str = "MiniMax-M2.7",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    streaming: bool = True,
    **kwargs,
) -> ChatOpenAI:
    """
    Create a MiniMax API client using LangChain's OpenAI-compatible interface.

    Args:
        model: MiniMax model name (default: MiniMax-M2.7)
        api_key: MiniMax API key (defaults to MINIMAX_API_KEY env var)
        api_base: MiniMax API base URL (defaults to MINIMAX_API_BASE env var)
        streaming: Enable streaming responses
        **kwargs: Additional arguments passed to ChatOpenAI

    Returns:
        ChatOpenAI client configured for MiniMax
    """
    return ChatOpenAI(
        model=model,
        openai_api_key=api_key or os.getenv("MINIMAX_API_KEY"),
        openai_api_base=api_base or os.getenv("MINIMAX_API_BASE", "https://api.minimax.chat/v1"),
        streaming=streaming,
        **kwargs,
    )
