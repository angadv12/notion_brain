"""Notification service for sending alerts via SMS and Telegram.

This module handles notification delivery, message formatting,
and quiet hours enforcement.
"""

import os
from datetime import datetime, time
from zoneinfo import ZoneInfo
from typing import Optional

import httpx

from src.config import settings
from src.schemas import RelatedTask


class NotificationService:
    """Service for sending notifications through various channels."""

    def __init__(self):
        self.timezone = ZoneInfo(settings.TIMEZONE)

    def is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours.

        Returns:
            True if notifications should be suppressed due to quiet hours
        """
        if not settings.QUIET_HOURS_ENABLED:
            return False

        now = datetime.now(self.timezone)
        current_time = now.time()

        try:
            start_time = time.fromisoformat(settings.QUIET_HOURS_START)
            end_time = time.fromisoformat(settings.QUIET_HOURS_END)
        except ValueError:
            print(f"Invalid quiet hours format: {settings.QUIET_HOURS_START}-{settings.QUIET_HOURS_END}")
            return False

        # Handle quiet hours that span midnight (e.g., 22:00 to 08:00)
        if start_time > end_time:
            # Quiet hours cross midnight
            return current_time >= start_time or current_time <= end_time
        else:
            # Normal quiet hours within same day
            return start_time <= current_time <= end_time

    def format_message(self, trigger_type: str, tasks: list[RelatedTask]) -> str:
        """Format notification message based on trigger type and tasks.

        Args:
            trigger_type: Type of notification trigger
            tasks: List of tasks to include in notification

        Returns:
            Formatted message string
        """
        if not tasks:
            return ""

        count = len(tasks)
        task_list = "\n".join([
            f"{i}. {task.title}"
            f"{' 📅 ' + task.due_date[:10] if task.due_date else ''}"
            f"{' 🔴' if task.priority == 'High' else ''}"
            for i, task in enumerate(tasks, 1)
        ])

        match trigger_type:
            case "overdue":
                emoji = "🔔"
                title = f"Overdue Tasks"
            case "urgent":
                emoji = "⚠️"
                title = f"Urgent Deadlines (within 4 hours)"
            case "today":
                emoji = "📅"
                title = f"Today's Tasks"
            case "tomorrow":
                emoji = "📆"
                title = f"Tomorrow's Tasks"
            case "high_priority":
                emoji = "🔴"
                title = f"High Priority Due Soon"
            case _:
                emoji = "📋"
                title = f"Task Reminder"

        return f"{emoji} {title} ({count}):\n{task_list}"

    async def send_sms(self, message: str) -> bool:
        """Send SMS notification via Twilio.

        Args:
            message: Message content to send

        Returns:
            True if SMS was sent successfully
        """
        if not settings.sms_enabled:
            print("SMS not configured, skipping")
            return False

        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"

        data = {
            "From": settings.TWILIO_PHONE_NUMBER,
            "To": settings.USER_PHONE_NUMBER,
            "Body": message
        }

        auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=data, auth=auth)
                if response.status_code in (200, 201):
                    print(f"SMS sent successfully")
                    return True
                else:
                    print(f"Twilio error: {response.text}")
                    return False
            except Exception as e:
                print(f"Error sending SMS: {e}")
                return False

    async def send_telegram(self, message: str) -> bool:
        """Send Telegram notification.

        Args:
            message: Message content to send

        Returns:
            True if message was sent successfully
        """
        if not settings.telegram_enabled:
            print("Telegram not configured, skipping")
            return False

        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

        data = {
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data)
                if response.status_code == 200:
                    print(f"Telegram message sent successfully")
                    return True
                else:
                    print(f"Telegram error: {response.text}")
                    return False
            except Exception as e:
                print(f"Error sending Telegram message: {e}")
                return False

    async def send_notification(
        self,
        trigger_type: str,
        tasks: list[RelatedTask],
        force: bool = False
    ) -> bool:
        """Send notification through enabled channels.

        Args:
            trigger_type: Type of notification trigger
            tasks: List of tasks to notify about
            force: If True, send even during quiet hours

        Returns:
            True if at least one notification was sent successfully
        """
        if not tasks:
            print(f"No tasks to notify for trigger: {trigger_type}")
            return False

        if not settings.NOTIFICATION_ENABLED:
            print("Notifications disabled in settings")
            return False

        if not force and self.is_quiet_hours():
            print(f"Quiet hours active, skipping notification")
            return False

        message = self.format_message(trigger_type, tasks)
        print(f"--- Sending notification: {trigger_type} ({len(tasks)} tasks) ---")
        print(f"Message:\n{message}")

        success = False
        channels = settings.enabled_channels

        if "sms" in channels:
            if await self.send_sms(message):
                success = True

        if "telegram" in channels:
            if await self.send_telegram(message):
                success = True

        return success


# Global notification service instance
notification_service = NotificationService()
