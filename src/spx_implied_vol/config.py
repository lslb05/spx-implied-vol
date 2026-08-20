"""Application configuration loaded from environment variables."""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime settings."""

    model_config = SettingsConfigDict(env_prefix="SPX_IMPLIED_VOL_", extra="ignore")

    log_level: str = "INFO"
    # No prefix on purpose: this is the same variable public-market-data
    # uses for its own connection — one DSN configures both projects.
    market_data_dsn: str = Field(
        default="postgresql://dados:dados@localhost:5433/dados_mercado_publico",
        validation_alias=AliasChoices("DADOS_MERCADO_PUBLICO_POSTGRES_DSN"),
    )
