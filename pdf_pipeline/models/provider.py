"""
Model provider - unified interface for LLMs and embeddings using LangChain.
"""
from dataclasses import dataclass
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings


@dataclass
class ModelConfig:
    """Configuration for a model."""
    provider: str  # "openai", "google", "anthropic", "ollama"
    model_name: str
    api_key: str = None
    extra_params: dict = None
    
    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


class ModelProvider:
    """
    Unified provider for LLM and embedding models.
    
    Supports: OpenAI, Google, Anthropic, Ollama, and more via LangChain.
    
    Usage:
        # Create provider with defaults
        provider = ModelProvider(
            llm_config=ModelConfig("openai", "gpt-4o-mini"),
            embedding_config=ModelConfig("openai", "text-embedding-3-small"),
        )
        
        # Get models
        llm = provider.get_llm()
        embeddings = provider.get_embeddings()
        
        # Or use different model for specific task
        google_llm = provider.create_llm(ModelConfig("google", "gemini-1.5-flash"))
    """
    
    def __init__(
        self,
        llm_config: ModelConfig = None,
        embedding_config: ModelConfig = None,
    ):
        self.llm_config = llm_config
        self.embedding_config = embedding_config
        self._llm = None
        self._embeddings = None
    
    def get_llm(self) -> BaseChatModel:
        """Get the default LLM instance."""
        if self._llm is None and self.llm_config:
            self._llm = self.create_llm(self.llm_config)
        return self._llm
    
    def get_embeddings(self) -> Embeddings:
        """Get the default embeddings instance."""
        if self._embeddings is None and self.embedding_config:
            self._embeddings = self.create_embeddings(self.embedding_config)
        return self._embeddings
    
    def create_llm(self, config: ModelConfig) -> BaseChatModel:
        """Create an LLM instance from config."""
        provider = config.provider.lower()
        
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.model_name,
                api_key=config.api_key,
                **config.extra_params,
            )
        
        elif provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=config.model_name,
                google_api_key=config.api_key,
                **config.extra_params,
            )
        
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=config.model_name,
                api_key=config.api_key,
                **config.extra_params,
            )
        
        elif provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=config.model_name,
                **config.extra_params,
            )
        
        elif provider == "bedrock":
            from langchain_aws import ChatBedrock
            return ChatBedrock(
                model_id=config.model_name,
                **config.extra_params,
            )
        
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    def create_embeddings(self, config: ModelConfig) -> Embeddings:
        """Create an embeddings instance from config."""
        provider = config.provider.lower()
        
        if provider == "openai":
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                model=config.model_name,
                api_key=config.api_key,
                **config.extra_params,
            )
        
        elif provider == "google":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(
                model=config.model_name,
                google_api_key=config.api_key,
                **config.extra_params,
            )
        
        elif provider == "ollama":
            from langchain_ollama import OllamaEmbeddings
            return OllamaEmbeddings(
                model=config.model_name,
                **config.extra_params,
            )
        
        elif provider == "bedrock":
            from langchain_aws import BedrockEmbeddings
            return BedrockEmbeddings(
                model_id=config.model_name,
                **config.extra_params,
            )
        
        elif provider == "huggingface":
            from langchain_huggingface import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(
                model_name=config.model_name,
                **config.extra_params,
            )
        
        else:
            raise ValueError(f"Unknown embedding provider: {provider}")


# Global default provider (can be set at startup)
_default_provider: ModelProvider = None


def get_default_provider() -> ModelProvider:
    """Get the global default model provider."""
    global _default_provider
    if _default_provider is None:
        # Create with defaults from environment
        import os
        _default_provider = ModelProvider(
            llm_config=ModelConfig(
                provider=os.getenv("LLM_PROVIDER", "openai"),
                model_name=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            ),
            embedding_config=ModelConfig(
                provider=os.getenv("EMBEDDING_PROVIDER", "openai"),
                model_name=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                api_key=os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            ),
        )
    return _default_provider


def set_default_provider(provider: ModelProvider):
    """Set the global default model provider."""
    global _default_provider
    _default_provider = provider
