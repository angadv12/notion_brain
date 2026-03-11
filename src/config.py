"""Configuration management for notion_brain using pydantic-settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Existing - Notion Integration
    NOTION_TOKEN: str
    NOTION_DATA_SOURCE_ID: str

    # Existing - Gemini AI
    GEMINI_API_KEY: str

    # Notification Settings - Twilio SMS
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    USER_PHONE_NUMBER: str = ""

    # Notification Settings - Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Notification Behavior
    NOTIFICATION_ENABLED: bool = True
    QUIET_HOURS_ENABLED: bool = True
    QUIET_HOURS_START: str = "22:00"
    QUIET_HOURS_END: str = "08:00"
    TIMEZONE: str = "America/New_York"

    # Notification Channels (comma-separated in env, converted to list)
    NOTIFICATION_CHANNELS: str = "sms"

    @property
    def enabled_channels(self) -> list[str]:
        """Parse comma-separated channels into a list."""
        return [ch.strip() for ch in self.NOTIFICATION_CHANNELS.split(",") if ch.strip()]

    @property
    def sms_enabled(self) -> bool:
        """Check if SMS notifications are enabled."""
        return "sms" in self.enabled_channels and bool(
            self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN
            and self.TWILIO_PHONE_NUMBER and self.USER_PHONE_NUMBER
        )

    @property
    def telegram_enabled(self) -> bool:
        """Check if Telegram notifications are enabled."""
        return "telegram" in self.enabled_channels and bool(
            self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID
        )


# Global settings instance
settings = Settings()
