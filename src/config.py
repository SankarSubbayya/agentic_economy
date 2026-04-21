from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    # API Keys
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Arc Testnet Configuration
    ARC_TESTNET_RPC: str = "https://rpc.arc.testnet.circle.com"
    ARC_TESTNET_CHAIN_ID: int = 42170

    # Wallet Addresses
    USER_WALLET: str = "0x742d35Cc6634C0532925a3b844Bc9e7595f"
    PROVIDER_WALLET: str = "0x8ba1f109a0E547B831995265700D2a04F"
    QUALITY_AGENT_WALLET: str = "0x9cb2f26A81e07cCde1de85C6d0Db4f4B5"
    SETTLEMENT_AGENT_WALLET: str = "0x1da2c4f01E07cCDe1de85C6d0Db4F4B"
    USER_PRIVATE_KEY: Optional[str] = None

    # Inference Settings
    MAX_TOKENS_PER_INFERENCE: int = 200
    MAX_BUDGET_USDC: float = 0.05

    # Quality Settings
    QUALITY_THRESHOLD: int = 75
    EVALUATION_INTERVAL: int = 10

    # Settlement Settings
    MOCK_SETTLEMENT: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    VERBOSE_LOGGING: bool = False


settings = Settings()
