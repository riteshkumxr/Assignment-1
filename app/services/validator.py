import re
from typing import Tuple


class RecipientValidator:
    """Validation logic for recipient data before certificate generation."""

    # Disallow control characters or absurd lengths
    MAX_NAME_LENGTH = 150
    MIN_NAME_LENGTH = 1

    @classmethod
    def validate_recipient(cls, name: str, email: str) -> Tuple[bool, str]:
        """
        Validate recipient name and email for runtime integrity.
        Returns (is_valid, error_message).
        """
        if not name or not name.strip():
            return False, "Recipient name cannot be empty."

        clean_name = name.strip()
        if len(clean_name) < cls.MIN_NAME_LENGTH or len(clean_name) > cls.MAX_NAME_LENGTH:
            return False, f"Recipient name length must be between {cls.MIN_NAME_LENGTH} and {cls.MAX_NAME_LENGTH} characters."

        # Check for control characters
        if re.search(r"[\x00-\x1f\x7f]", clean_name):
            return False, "Recipient name contains illegal control characters."

        if not email or not email.strip():
            return False, "Recipient email cannot be empty."

        clean_email = email.strip()
        # Basic email format check
        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_pattern, clean_email):
            return False, f"Invalid email address format: '{clean_email}'"

        return True, ""
