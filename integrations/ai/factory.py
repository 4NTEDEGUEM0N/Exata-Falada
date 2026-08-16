from config import settings
from .base import AIProvider
from .gemini_provider import GeminiProvider

class AIFactory:
    """Factory para instanciar o provedor de Inteligência Artificial ativo."""

    @staticmethod
    def get_provider(provider_name: str | None = None) -> AIProvider:
        selected = provider_name or settings.AI_PROVIDER
        
        if selected == "gemini":
            return GeminiProvider(api_key=settings.GOOGLE_API_KEY)
            
        raise ValueError(f"Provedor de IA desconhecido: '{selected}'")
