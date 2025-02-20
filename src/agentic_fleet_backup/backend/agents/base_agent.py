from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import logging
from dataclasses import dataclass, field
from enum import Enum, auto

class AgentState(Enum):
    """
    Represents the possible states of an agent during its lifecycle.
    
    Attributes:
        INITIALIZED: Agent has been created but not started
        RUNNING: Agent is currently executing a task
        IDLE: Agent is waiting for a task
        ERROR: Agent encountered an error during execution
        COMPLETED: Agent has successfully completed its task
    """
    INITIALIZED = auto()
    RUNNING = auto()
    IDLE = auto()
    ERROR = auto()
    COMPLETED = auto()

@dataclass
class BaseAgentState:
    """
    Represents the internal state of a BaseAgent.
    
    Attributes:
        current_state (AgentState): Current state of the agent
        task_history (List[Dict[str, Any]]): History of tasks executed
        error_log (List[str]): Log of errors encountered
        capabilities (Dict[str, Any]): Agent's capabilities and configurations
    """
    current_state: AgentState = field(default=AgentState.INITIALIZED)
    task_history: List[Dict[str, Any]] = field(default_factory=list)
    error_log: List[str] = field(default_factory=list)
    capabilities: Dict[str, Any] = field(default_factory=dict)

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the AgenticFleet system.
    
    Provides a standardized interface for agent initialization, 
    task execution, error handling, and state management.
    
    Attributes:
        name (str): Unique identifier for the agent
        state (BaseAgentState): Internal state of the agent
        logger (logging.Logger): Logger for tracking agent activities
    
    Methods:
        initialize(): Set up the agent's initial state and resources
        execute_task(task): Abstract method to execute a given task
        handle_error(error): Handle and log errors during task execution
        reset_state(): Reset the agent to its initial state
    """
    
    def __init__(self, 
                 name: str, 
                 capabilities: Optional[Dict[str, Any]] = None):
        """
        Initialize a BaseAgent.
        
        Args:
            name (str): Unique name for the agent
            capabilities (Dict[str, Any], optional): Agent's specific capabilities
        """
        self.name = name
        self.state = BaseAgentState(
            capabilities=capabilities or {}
        )
        self.logger = logging.getLogger(f"AgenticFleet.Agent.{name}")
    
    def initialize(self) -> None:
        """
        Initialize the agent's resources and prepare for task execution.
        
        This method can be overridden by subclasses to provide 
        specific initialization logic.
        """
        self.state.current_state = AgentState.IDLE
        self.logger.info(f"Agent {self.name} initialized successfully")
    
    @abstractmethod
    def execute_task(self, task: Any) -> Any:
        """
        Execute a given task. Must be implemented by subclasses.
        
        Args:
            task (Any): The task to be executed
        
        Returns:
            Any: Result of task execution
        
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement execute_task method")
    
    def handle_error(self, error: Exception) -> None:
        """
        Handle and log errors during task execution.
        
        Args:
            error (Exception): The error encountered
        """
        self.state.current_state = AgentState.ERROR
        error_message = f"Agent {self.name} encountered an error: {str(error)}"
        self.logger.error(error_message)
        self.state.error_log.append(error_message)
    
    def reset_state(self) -> None:
        """
        Reset the agent to its initial state, clearing task history and errors.
        """
        self.state = BaseAgentState(
            capabilities=self.state.capabilities
        )
        self.initialize()
        self.logger.info(f"Agent {self.name} state reset")
    
    def log_task(self, task: Dict[str, Any]) -> None:
        """
        Log a completed task in the agent's task history.
        
        Args:
            task (Dict[str, Any]): Details of the completed task
        """
        self.state.task_history.append(task)
        self.logger.info(f"Task logged for agent {self.name}: {task}")