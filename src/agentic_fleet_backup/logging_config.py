import logging

def configure_logging():
    """Configure logging for AgenticFleet."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ) 