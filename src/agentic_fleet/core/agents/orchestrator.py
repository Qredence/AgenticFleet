"""
Orchestrator agent for AgenticFleet.

This module implements the lead orchestrator agent responsible for:
- Task decomposition and planning
- Directing other agents
- Tracking progress
- Managing task and progress ledgers
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from autogen_core.models import ChatCompletionClient
from pydantic import BaseModel

from agentic_fleet.core.agents.base import BaseAgent
from agentic_fleet.core.models.messages import EnhancedSystemMessage

logger = logging.getLogger(__name__)

# Orchestrator prompts
ORCHESTRATOR_SYSTEM_MESSAGE = ""

ORCHESTRATOR_CLOSED_BOOK_PROMPT = """Below I will present you a request. Before we begin addressing the request, please answer the following pre-survey to the best of your ability. Keep in mind that you are Ken Jennings-level with trivia, and Mensa-level with puzzles, so there should be a deep well to draw from.

Here is the request:

{task}

Here is the pre-survey:

1. Please list any specific facts or figures that are GIVEN in the request itself. It is possible that there are none.

2. Please list any facts that may need to be looked up, and WHERE SPECIFICALLY they might be found. In some cases, authoritative sources are mentioned in the request itself.

3. Please list any facts that may need to be derived (e.g., via logical deduction, simulation, or computation)

4. Please list any facts that are recalled from memory, hunches, well-reasoned guesses, etc.

When answering this survey, keep in mind that "facts" will typically be specific names, dates, statistics, etc. Your answer should use headings:

1. GIVEN OR VERIFIED FACTS

2. FACTS TO LOOK UP

3. FACTS TO DERIVE

4. EDUCATED GUESSES

DO NOT include any other headings or sections in your response. DO NOT list next steps or plans until asked to do so.
"""

ORCHESTRATOR_PLAN_PROMPT = """Fantastic. To address this request we have assembled the following team:

{team}

Based on the team composition, and known and unknown facts, please devise a short bullet-point plan for addressing the original request. Remember, there is no requirement to involve all team members -- a team member's particular expertise may not be needed for this task."""

ORCHESTRATOR_SYNTHESIZE_PROMPT = """
We are working to address the following user request:

{task}

To answer this request we have assembled the following team:

{team}

Here is an initial fact sheet to consider:

{facts}

Here is the plan to follow as best as possible:

{plan}
"""

ORCHESTRATOR_LEDGER_PROMPT = """
Recall we are working on the following request:

{task}

And we have assembled the following team:

{team}

To make progress on the request, please answer the following questions, including necessary reasoning:

- Is the request fully satisfied? (True if complete, or False if the original request has yet to be SUCCESSFULLY and FULLY addressed)

- Are we in a loop where we are repeating the same requests and / or getting the same responses as before? Loops can span multiple turns, and can include repeated actions like scrolling up or down more than a handful of times.

- Are we making forward progress? (True if just starting, or recent messages are adding value. False if recent messages show evidence of being stuck in a loop or if there is evidence of significant barriers to success such as the inability to read from a required file)

- Who should speak next? (select from: {names})

- What instruction or question would you give this team member? (Phrase as if speaking directly to them, and include any specific information they may need)

Please output an answer in pure JSON format according to the following schema. The JSON object must be parsable as-is. DO NOT OUTPUT ANYTHING OTHER THAN JSON, AND DO NOT DEVIATE FROM THIS SCHEMA:

{{
"is_request_satisfied": {{
    "reason": string,
    "answer": boolean
}},
"is_in_loop": {{
    "reason": string,
    "answer": boolean
}},
"is_progress_being_made": {{
    "reason": string,
    "answer": boolean
}},
"next_speaker": {{
    "reason": string,
    "answer": string (select from: {names})
}},
"instruction_or_question": {{
    "reason": string,
    "answer": string
}}
}}
"""

ORCHESTRATOR_UPDATE_FACTS_PROMPT = """As a reminder, we are working to solve the following task:

{task}

It's clear we aren't making as much progress as we would like, but we may have learned something new. Please rewrite the following fact sheet, updating it to include anything new we have learned that may be helpful. Example edits can include (but are not limited to) adding new guesses, moving educated guesses to verified facts if appropriate, etc. Updates may be made to any section of the fact sheet, and more than one section of the fact sheet can be edited. This is an especially good time to update educated guesses, so please at least add or update one educated guess or hunch, and explain your reasoning.

Here is the old fact sheet:

{facts}
"""

ORCHESTRATOR_UPDATE_PLAN_PROMPT = """Please briefly explain what went wrong on this last run (the root cause of the failure), and then come up with a new plan that takes steps and/or includes hints to overcome prior challenges and especially avoids repeating the same mistakes. As before, the new plan should be concise, be expressed in bullet-point form, and consider the following team composition (do not involve any other outside people since we cannot contact anyone else):

{team}
"""

ORCHESTRATOR_GET_FINAL_ANSWER = """
We are working on the following task:

{task}

We have completed the task.

The above messages contain the conversation that took place to complete the task.

Based on the information gathered, provide the final answer to the original request.

The answer should be phrased as if you were speaking to the user.
"""


@dataclass
class TaskEntry:
    """Entry in the task ledger."""

    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    assigned_agent: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    result: Any | None = None
    facts: dict[str, list[str]] = field(
        default_factory=lambda: {
            "GIVEN OR VERIFIED FACTS": [],
            "FACTS TO LOOK UP": [],
            "FACTS TO DERIVE": [],
            "EDUCATED GUESSES": [],
        }
    )
    plan: list[str] = field(default_factory=list)


class TaskLedger:
    """Maintains the history and state of tasks."""

    def __init__(self):
        """Initialize the task ledger."""
        self.tasks: list[TaskEntry] = []
        self.current_task_index: int = 0

    def add_task(self, description: str) -> TaskEntry:
        """Add a new task to the ledger."""
        task = TaskEntry(description=description)
        self.tasks.append(task)
        return task

    def update_task(self, index: int, **updates) -> None:
        """Update a task's attributes."""
        if 0 <= index < len(self.tasks):
            task = self.tasks[index]
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            if updates.get("status") == "completed":
                task.completed_at = datetime.now()

    def get_current_task(self) -> TaskEntry | None:
        """Get the current active task."""
        if 0 <= self.current_task_index < len(self.tasks):
            return self.tasks[self.current_task_index]
        return None


class ProgressLedger:
    """Tracks progress and maintains state for self-reflection."""

    def __init__(self):
        """Initialize the progress ledger."""
        self.steps: list[dict[str, Any]] = []
        self.stall_count: int = 0
        self.last_progress_time: datetime = datetime.now()

    def add_step(self, description: str, result: Any = None) -> None:
        """Add a new progress step."""
        self.steps.append(
            {"description": description, "result": result, "timestamp": datetime.now()}
        )
        self.last_progress_time = datetime.now()

    def is_stalled(self, stall_threshold_seconds: int = 300) -> bool:
        """Check if progress is stalled."""
        time_since_last_progress = (datetime.now() - self.last_progress_time).total_seconds()
        return time_since_last_progress > stall_threshold_seconds


class OrchestratorConfig(BaseModel):
    """Configuration for the Orchestrator agent."""

    max_stalls: int = 3
    stall_threshold_seconds: int = 300
    max_steps: int = 50
    planning_temperature: float = 0.7
    default_system_message: str = (
        "You are the lead orchestrator agent responsible for planning and coordinating other agents to complete tasks."
    )


class Orchestrator(BaseAgent):
    """
    Lead orchestrator agent that coordinates other agents to complete tasks.

    The orchestrator:
    1. Creates and maintains task plans
    2. Assigns subtasks to appropriate agents
    3. Tracks progress and handles failures
    4. Updates plans when progress stalls
    """

    def __init__(
        self,
        name: str = "orchestrator",
        config: OrchestratorConfig | None = None,
        model_client: ChatCompletionClient | None = None,
        available_agents: dict[str, BaseAgent] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Orchestrator agent.

        Args:
            name: Name of this orchestrator instance
            config: Configuration settings
            model_client: The LLM client to use
            available_agents: Dictionary of available agents to coordinate
            **kwargs: Additional keyword arguments
        """
        super().__init__(name=name, model_client=model_client, **kwargs)

        self.config = config or OrchestratorConfig()
        self.available_agents = available_agents or {}

        self.task_ledger = TaskLedger()
        self.progress_ledger = ProgressLedger()

    async def _get_facts(self, task: str) -> dict[str, list[str]]:
        """Gather initial facts about the task using closed book prompt."""
        system_message = EnhancedSystemMessage(
            content=ORCHESTRATOR_CLOSED_BOOK_PROMPT.format(task=task), source="system"
        )

        response = await self.model_client.chat_completion(
            messages=[system_message], temperature=self.config.planning_temperature
        )

        # Parse response into fact categories
        facts = {
            "GIVEN OR VERIFIED FACTS": [],
            "FACTS TO LOOK UP": [],
            "FACTS TO DERIVE": [],
            "EDUCATED GUESSES": [],
        }

        current_category = None
        for line in response.content.split("\n"):
            line = line.strip()
            if line in facts:
                current_category = line
            elif current_category and line:
                facts[current_category].append(line)

        return facts

    async def create_task_plan(self, task: str) -> list[str]:
        """Create a plan of subtasks for the given task."""
        # First gather facts
        facts = await self._get_facts(task)

        # Create plan using the facts
        system_message = EnhancedSystemMessage(
            content=ORCHESTRATOR_PLAN_PROMPT.format(
                team=self._format_agent_capabilities(), task=task
            ),
            source="system",
        )

        response = await self.model_client.chat_completion(
            messages=[system_message], temperature=self.config.planning_temperature
        )

        # Parse response into subtasks
        subtasks = self._parse_plan_into_subtasks(response.content)

        # Create task entry with facts and plan
        task_entry = self.task_ledger.add_task(task)
        task_entry.facts = facts
        task_entry.plan = subtasks

        return subtasks

    def _format_agent_capabilities(self) -> str:
        """Format available agents and their capabilities."""
        capabilities = []
        for name, agent in self.available_agents.items():
            desc = getattr(agent, "description", "No description available")
            capabilities.append(f"- {name}: {desc}")
        return "\n".join(capabilities)

    def _parse_plan_into_subtasks(self, plan: str) -> list[str]:
        """Parse the LLM response into discrete subtasks."""
        subtasks = [
            line.strip().lstrip("- ").lstrip("* ")
            for line in plan.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        return subtasks

    async def assign_task(self, task: TaskEntry) -> str | None:
        """Assign a task to the most appropriate agent."""
        # Use ledger prompt to determine next agent and action
        names = list(self.available_agents.keys())
        ledger_response = await self.model_client.chat_completion(
            messages=[
                EnhancedSystemMessage(
                    content=ORCHESTRATOR_LEDGER_PROMPT.format(
                        task=task.description,
                        team=self._format_agent_capabilities(),
                        names=", ".join(names),
                    ),
                    source="system",
                )
            ],
            temperature=0.2,
        )

        try:
            import json

            decision = json.loads(ledger_response.content)
            return decision["next_speaker"]["answer"]
        except (json.JSONDecodeError, KeyError):
            logger.error("Failed to parse ledger response")
            return None

    async def execute_task(self, task: str) -> Any:
        """Execute a complete task using available agents."""
        # Create initial plan
        await self.create_task_plan(task)
        current_task = self.task_ledger.get_current_task()

        while current_task and not current_task.status == "completed":
            # Check for stall conditions
            if self.progress_ledger.is_stalled(self.config.stall_threshold_seconds):
                self.progress_ledger.stall_count += 1
                if self.progress_ledger.stall_count >= self.config.max_stalls:
                    # Update facts and create new plan
                    await self._update_facts_and_plan(current_task)
                    continue

            # Assign and execute subtask
            agent_name = await self.assign_task(current_task)
            if agent_name and agent_name in self.available_agents:
                agent = self.available_agents[agent_name]
                try:
                    result = await agent.execute(current_task.description)
                    self.task_ledger.update_task(
                        self.task_ledger.current_task_index,
                        status="completed",
                        result=result,
                        assigned_agent=agent_name,
                    )
                    self.progress_ledger.add_step(
                        f"Completed subtask: {current_task.description}", result=result
                    )
                except Exception as e:
                    logger.error(f"Task execution failed: {str(e)}")
                    self.task_ledger.update_task(
                        self.task_ledger.current_task_index,
                        status="failed",
                        assigned_agent=agent_name,
                    )
                    # Update plan on failure
                    await self._update_facts_and_plan(current_task)

            self.task_ledger.current_task_index += 1
            current_task = self.task_ledger.get_current_task()

        # Get final answer
        final_response = await self.model_client.chat_completion(
            messages=[
                EnhancedSystemMessage(
                    content=ORCHESTRATOR_GET_FINAL_ANSWER.format(task=task), source="system"
                )
            ],
            temperature=0.7,
        )

        return final_response.content

    async def _update_facts_and_plan(self, task: TaskEntry) -> None:
        """Update facts and create new plan when progress stalls."""
        # Update facts
        facts_response = await self.model_client.chat_completion(
            messages=[
                EnhancedSystemMessage(
                    content=ORCHESTRATOR_UPDATE_FACTS_PROMPT.format(
                        task=task.description, facts=task.facts
                    ),
                    source="system",
                )
            ],
            temperature=0.7,
        )

        # Update plan
        plan_response = await self.model_client.chat_completion(
            messages=[
                EnhancedSystemMessage(
                    content=ORCHESTRATOR_UPDATE_PLAN_PROMPT.format(
                        team=self._format_agent_capabilities()
                    ),
                    source="system",
                )
            ],
            temperature=0.7,
        )

        # Update task with new facts and plan
        new_plan = self._parse_plan_into_subtasks(plan_response.content)
        self.task_ledger.update_task(self.task_ledger.current_task_index, plan=new_plan)

    async def execute(self, task: str) -> Any:
        """Execute a task (implementation of BaseAgent method)."""
        return await self.execute_task(task)
