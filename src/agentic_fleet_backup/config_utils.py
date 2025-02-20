import logging
import os

from agentic_fleet.config import config_manager

logger = logging.getLogger(__name__)

def load_all_configurations():
    try:
        config_manager.load_all()
        logger.info("Successfully loaded all configurations")
        error = config_manager.validate_environment()
        if error:
            raise ValueError(error)
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        raise


def check_oauth_configuration():
    try:
        security_config = config_manager.get_security_settings()
        oauth_providers = security_config.get("oauth_providers", [])
        required_vars = {}
        for provider in oauth_providers:
            required_vars[provider["client_id_env"]] = os.getenv(provider["client_id_env"])
            required_vars[provider["client_secret_env"]] = os.getenv(provider["client_secret_env"])
        required_vars["OAUTH_REDIRECT_URI"] = os.getenv("OAUTH_REDIRECT_URI")
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            return f"Missing required OAuth environment variables: {', '.join(missing_vars)}"
        if not oauth_providers:
            return "No OAuth providers configured"
        return None
    except Exception as e:
        logger.error(f"Error checking OAuth configuration: {str(e)}")
        return f"Failed to check OAuth configuration: {str(e)}"


async def cleanup_workspace():
    try:
        env_config = config_manager.get_environment_settings()
        workspace_dir = os.path.join(os.getcwd(), env_config["workspace_dir"])
        if os.path.exists(workspace_dir):
            import shutil
            shutil.rmtree(workspace_dir)
            logger.info("Workspace cleaned up successfully")
    except Exception as e:
        logger.error(f"Failed to clean up workspace: {str(e)}")


def get_workspace_dir():
    try:
        env_config = config_manager.get_environment_settings()
        return os.path.join(os.getcwd(), env_config["workspace_dir"])
    except Exception as e:
        logger.error(f"Failed to get workspace directory: {str(e)}")
        return None
