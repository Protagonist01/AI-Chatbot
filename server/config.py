from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API
    api_secret_key: str
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Supabase
    supabase_url: str
    supabase_key: str
    
    # n8n
    n8n_webhook_base_url: str
    n8n_agent_message_webhook: str
    n8n_takeover_webhook: str
    
    # OpenAI
    openai_api_key: str
    
    # CORS
    allowed_origins: str = "*"
    
    @property
    def origins_list(self) -> List[str]:
        """Parse comma-separated origins"""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()