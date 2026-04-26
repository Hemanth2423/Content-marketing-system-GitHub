from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    anthropic_api_key: str
    zernio_api_key: str = ""
    firecrawl_api_key: str = ""
    firecrawl_max_results: int = 5
    mailgun_api_key: str = "dummy"
    mailgun_domain: str = "sandbox.mailgun.org"
    mailgun_from: str = "noreply@sandbox.mailgun.org"
    mailgun_to: str = "team@github-marketing.com"

    # Paths
    data_dir: Path = BASE_DIR / "data"
    company_data_dir: Path = BASE_DIR / "data" / "company_data"
    storage_dir: Path = BASE_DIR / "storage"
    chroma_db_dir: Path = BASE_DIR / "data" / "chroma_db"

    # ChromaDB
    chroma_collection: str = "github_knowledge_base"
    retrieval_top_k: int = 10
    retrieval_min_score: float = 0.4
    low_context_threshold: int = 3

    # SLA windows in seconds (demo-compressed)
    sla_strategist_seconds: int = 30
    sla_reviewer_seconds: int = 45
    sla_publisher_seconds: int = 15
    sla_warning_pct: float = 0.5   # yellow alert threshold
    sla_urgent_pct: float = 0.8    # red + email threshold
    publish_window_warning_seconds: int = 7200  # 2 hours

    # Draft revision
    max_draft_revisions: int = 2

    # Models
    model_haiku: str = "claude-haiku-4-5"
    model_sonnet: str = "claude-sonnet-4-6"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        protected_namespaces=("settings_",),
        env_ignore_empty=True,
    )


settings = Settings()
