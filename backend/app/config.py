from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Plantagenet Planning Advisor API"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    host: str = "0.0.0.0"
    port: int = 8000

    # Policy RAG (Supabase pgvector) — same DB filled by policy_rag upload
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # LLM for written answers: auto | huggingface | groq | gemini
    llm_provider: str = "auto"

    # Hugging Face Inference Providers (free monthly credits with HF account)
    # Create token: https://huggingface.co/settings/tokens (enable Inference)
    hf_token: str = ""
    hf_model: str = "Qwen/Qwen2.5-7B-Instruct"

    # Groq free API — recommended free option (fast Llama)
    # Create key: https://console.groq.com/keys
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    # Google Gemini (optional fallback)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"

    # Simple 2-hop RAG: retrieve → follow-up search → merge → answer
    multi_hop: bool = True
    multi_hop_match_count: int = 10
    multi_hop_final_count: int = 12

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
