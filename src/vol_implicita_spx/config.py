"""Application configuration loaded from environment variables."""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime settings."""

    model_config = SettingsConfigDict(env_prefix="VOL_IMPLICITA_SPX_", extra="ignore")

    log_level: str = "INFO"
    # Sem prefixo de propósito: é a mesma variável que o dados-mercado-publico
    # usa para a própria conexão — um único DSN configura os dois projetos.
    dados_mercado_publico_dsn: str = Field(
        default="postgresql://dados:dados@localhost:5433/dados_mercado_publico",
        validation_alias=AliasChoices("DADOS_MERCADO_PUBLICO_POSTGRES_DSN"),
    )
