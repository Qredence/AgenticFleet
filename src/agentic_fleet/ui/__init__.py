"""UI module for Agentic Fleet."""

# Standard library imports
import logging
from importlib.util import find_spec
from typing import Any

# Initialize logging
logger = logging.getLogger(__name__)

# Apply patches for Chainlit LiteralAI integration if needed
#
# This includes:
# 1. A patch for StepType enum compatibility issues in LiteralDataLayer.create_step
# 2. A patch for the deprecated datetime.utcnow() usage in literalai.helper
#    (This fixes the warning: "datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version.
#     Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).")
try:
    if find_spec("chainlit") and find_spec("literalai"):
        import datetime as dt_module

        import literalai.helper
        from chainlit.data.literalai import LiteralDataLayer

        # Store original datetime module in literalai.helper
        original_datetime = literalai.helper.datetime

        # Create a patched datetime module with a fixed utcnow method
        class PatchedDatetime(dt_module.datetime):
            @classmethod
            def utcnow(cls):
                """Patched utcnow method that uses now(UTC) instead.

                This replaces the deprecated datetime.utcnow() with datetime.now(UTC).
                The timezone information is removed to ensure compatibility with APIs
                that expect naive datetime objects.

                Returns:
                    A naive datetime object representing the current UTC time
                """
                # Get timezone-aware datetime and then remove timezone info
                dt = dt_module.datetime.now(dt_module.UTC)
                return dt.replace(tzinfo=None)

        # Replace the datetime module in literalai.helper with our patched version
        literalai.helper.datetime = PatchedDatetime

        # Store original create_step method
        original_create_step = LiteralDataLayer.create_step

        async def patched_create_step(self, step_dict: Any) -> Any:
            """Patch to fix StepType enum compatibility issues.

            This patches the incorrect step type values to match the required enum values
            in LiteralAI API.

            Args:
                self: The LiteralDataLayer instance
                step_dict: The step dictionary to be sent

            Returns:
                The result of the original create_step method
            """
            # Fix the step type if needed
            if step_dict.get("type") == "system":
                step_dict["type"] = "system_message"
            elif step_dict.get("type") == "user":
                step_dict["type"] = "user_message"
            elif step_dict.get("type") == "assistant":
                step_dict["type"] = "assistant_message"

            # Call original method with fixed step_dict
            return await original_create_step(self, step_dict)

        # Apply the monkey patches - using a safer approach
        # Patch LiteralDataLayer.create_step
        if hasattr(LiteralDataLayer, "create_step"):
            setattr(LiteralDataLayer, "create_step", patched_create_step)
            logger.info("Applied patch to LiteralDataLayer.create_step for StepType compatibility")

        # Log the datetime module patch
        logger.info(
            "Applied patch to literalai.helper.datetime to fix datetime.utcnow() deprecation"
        )

except Exception as e:
    logger.warning(f"Failed to apply LiteralAI patch: {str(e)}")
