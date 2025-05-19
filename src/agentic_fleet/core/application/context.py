"""Application context module for AgenticFleet."""

from typing import Any, Dict, Optional

from agentic_fleet.core.application.manager import ApplicationManager
from agentic_fleet.config import ConfigurationManager as ConfigManager


class ApplicationContext:
    """Application context for AgenticFleet.
    
    This class encapsulates the application state and provides access to
    core components like the application manager, configuration manager,
    and model client.
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        app_manager: ApplicationManager,
        model_client: Any,
    ) -> None:
        """Initialize the application context.
        
        Args:
            config_manager: Configuration manager instance
            app_manager: Application manager instance
            model_client: Model client instance
        """
        self.config_manager = config_manager
        self.app_manager = app_manager
        self.model_client = model_client
        self.metadata: Dict[str, Any] = {}
        
    async def shutdown(self) -> None:
        """Shutdown the application context and clean up resources."""
        if self.app_manager:
            await self.app_manager.shutdown()
            
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)
