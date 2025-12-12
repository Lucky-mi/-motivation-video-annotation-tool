# backend/ai_providers/__init__.py
"""
AI Provider模块 - 支持多种VLM模型
"""

from .base_provider import BaseAIProvider, AIProviderFactory
from .openai_provider import OpenAIProvider

# 尝试导入可选的provider
try:
    from .gemini_provider import GeminiProvider
    GEMINI_AVAILABLE = True
except ImportError:
    GeminiProvider = None
    GEMINI_AVAILABLE = False

__all__ = [
    'BaseAIProvider',
    'AIProviderFactory',
    'OpenAIProvider',
    'GeminiProvider',
    'GEMINI_AVAILABLE'
]
