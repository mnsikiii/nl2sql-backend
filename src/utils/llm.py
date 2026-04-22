"""LLM client management"""
from openai import OpenAI

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

_openai_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    """
    Get or create the OpenAI client.
    
    Returns:
        OpenAI client instance
    """
    global _openai_client
    
    if _openai_client is None:
        logger.info("Initializing OpenAI client...")
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("OpenAI client initialized")
    
    return _openai_client
