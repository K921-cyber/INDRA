import re
from typing import Optional


class AutoDetect:
    """Auto-detect search target type: domain, IP, email, phone, or name."""

    IP_PATTERN = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    DOMAIN_PATTERN = re.compile(r"^([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")
    PHONE_PATTERN = re.compile(r"^\+?[\d\s\-\(\)]{7,15}$")

    @classmethod
    def detect(cls, target: str) -> str:
        """Detect target type. Returns: domain, ip, email, phone, name, unknown."""
        target = target.strip().lower()

        if cls.IP_PATTERN.match(target):
            return "ip"
        if cls.EMAIL_PATTERN.match(target):
            return "email"
        if cls.PHONE_PATTERN.match(target):
            return "phone"
        if cls.DOMAIN_PATTERN.match(target):
            return "domain"
        return "name"

    @classmethod
    def detect_full(cls, target: str) -> dict:
        """Return full detection info with confidence score."""
        target_type = cls.detect(target)

        confidence_map = {
            "ip": 1.0,
            "email": 1.0,
            "phone": 0.85,
            "domain": 0.95,
            "name": 0.6,
            "unknown": 0.0,
        }

        return {
            "target": target.strip(),
            "detected_type": target_type,
            "confidence": confidence_map.get(target_type, 0.0),
        }

    @classmethod
    def get_display_label(cls, target_type: str) -> str:
        labels = {
            "domain": "🌐 Domain",
            "ip": "📍 IP Address",
            "email": "📧 Email",
            "phone": "📱 Phone",
            "name": "👤 Person",
            "unknown": "❓ Unknown",
        }
        return labels.get(target_type, "❓ Unknown")


