import os
from pathlib import Path
from typing import Optional

from dotenv import dotenv_values
from langchain_openai import ChatOpenAI

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = BACKEND_ROOT / ".env"


def resolve_minimax_config(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    env_file: Optional[Path] = None,
) -> dict:
    """
    Resolve MiniMax settings, preferring the current .env file over process env.

    This allows local key changes to take effect without restarting the backend.
    """
    env_path = env_file or DEFAULT_ENV_FILE
    file_values = dotenv_values(env_path) if env_path.exists() else {}

    resolved_model = model if model is not None else (
        file_values.get("MINIMAX_CHAT_MODEL")
        or os.getenv("MINIMAX_CHAT_MODEL")
        or "MiniMax-M2.7"
    )
    resolved_api_key = api_key if api_key is not None else (
        file_values.get("MINIMAX_API_KEY")
        or os.getenv("MINIMAX_API_KEY")
    )
    resolved_api_base = api_base if api_base is not None else (
        file_values.get("MINIMAX_API_BASE")
        or os.getenv("MINIMAX_API_BASE", "https://api.minimax.chat/v1")
    )

    return {
        "model": resolved_model,
        "api_key": resolved_api_key,
        "api_base": resolved_api_base,
    }


def get_minimax_client(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    streaming: bool = True,
    env_file: Optional[Path] = None,
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
    config = resolve_minimax_config(
        model=model,
        api_key=api_key,
        api_base=api_base,
        env_file=env_file,
    )

    return ChatOpenAI(
        model=config["model"],
        openai_api_key=config["api_key"],
        openai_api_base=config["api_base"],
        streaming=streaming,
        **kwargs,
    )
