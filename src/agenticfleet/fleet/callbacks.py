"""Event callbacks for Magentic workflow observability."""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Protocol

from agenticfleet.cli.ui import AgentMessage, FinalRenderData
from agenticfleet.core.logging import get_logger

if TYPE_CHECKING:
    from agent_framework import ChatMessage

logger = get_logger(__name__)


class ConsoleUIProtocol(Protocol):
    """Protocol describing the ConsoleUI interface used by callbacks."""

    def log_agent_message(self, message: AgentMessage) -> None:
        pass

    def log_plan(
        self,
        facts: list[str] | tuple[str, ...] | None,
        plan: list[str] | tuple[str, ...] | None,
    ) -> None:
        pass

    def log_progress(
        self,
        status: str,
        next_speaker: str,
        instruction: str | None = None,
    ) -> None:
        pass

    def log_notice(self, text: str, *, style: str = "blue") -> None:
        pass

    def log_final(self, result: Any) -> None:
        pass


def _coerce_lines(value: Any) -> list[str]:
    """Convert various ledger data structures into readable bullet lines."""

    if value is None:
        return []

    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]

    if isinstance(value, dict):
        return [f"{key}: {val}" for key, val in value.items()]

    items = value if isinstance(value, list | tuple | set) else [value]
    lines: list[str] = []

    for item in items:
        if item is None:
            continue
        for attr in ("summary", "description", "text", "content", "instruction"):
            if hasattr(item, attr):
                text = getattr(item, attr)
                if isinstance(text, str) and text.strip():
                    lines.append(text.strip())
                    break
        else:
            text = str(item).strip()
            if text and not text.startswith("WorkflowStatusEvent"):
                lines.append(text)

    return lines


def _extract_agent_name(message: Any) -> str:
    for attr in ("agent_name", "participant_id", "name", "role"):
        if hasattr(message, attr):
            value = getattr(message, attr)
            if value:
                return str(value)
    return "agent"


def _extract_text(message: Any) -> str:
    if isinstance(message, str):
        return message
    for attr in ("delta", "text", "content", "message"):
        if hasattr(message, attr):
            value = getattr(message, attr)
            if isinstance(value, str):
                return value
            if isinstance(value, list | tuple):
                parts: list[str] = []
                for part in value:
                    if part is None:
                        continue
                    if isinstance(part, str):
                        text = part.strip()
                        if text:
                            parts.append(text)
                            continue
                    if isinstance(part, dict):
                        for key in ("text", "content", "message", "value"):
                            maybe = part.get(key)
                            if isinstance(maybe, str):
                                text = maybe.strip()
                                if text:
                                    parts.append(text)
                                    break
                        else:
                            text = str(part).strip()
                            if text:
                                parts.append(text)
                        continue
                    text = str(part).strip()
                    if text:
                        parts.append(text)
                if parts:
                    return "\n".join(parts)
    return str(message)


def _first_available(source: Any, *names: str) -> Any:
    for name in names:
        if isinstance(source, dict) and name in source:
            value = source[name]
            if value is not None:
                return value
        if hasattr(source, name):
            value = getattr(source, name)
            if value is not None:
                return value
    return None


class ConsoleCallbacks:
    """Adapter that relays Magentic events to the active console UI."""

    def __init__(self, ui: ConsoleUIProtocol | None = None) -> None:
        self._ui = ui
        self._agent_stream_cache: ContextVar[dict[str, list[str]] | None] = ContextVar(
            "agent_stream_cache",
            default=None,
        )
        self._final_render: ContextVar[FinalRenderData | None] = ContextVar(
            "final_render_data",
            default=None,
        )

    @property
    def ui(self) -> ConsoleUIProtocol | None:
        return self._ui

    def set_ui(self, ui: ConsoleUIProtocol | None) -> None:
        """Update the console UI sink used for rendering events."""

        self._ui = ui

    def _get_ui(self) -> ConsoleUIProtocol | None:
        return self._ui

    def _get_stream_cache(self) -> dict[str, list[str]]:
        cache = self._agent_stream_cache.get()
        if cache is None:
            cache = {}
            self._agent_stream_cache.set(cache)
        return cache

    async def agent_delta_callback(self, event: Any) -> None:
        """Buffer streaming deltas without flooding the console."""

        agent_name = _extract_agent_name(event)
        text = _extract_text(event).strip()
        if not text:
            return
        cache = self._get_stream_cache()
        cache.setdefault(agent_name, []).append(text)

    async def agent_message_callback(self, message: Any) -> None:
        """Display the final aggregated agent response."""

        agent_name = _extract_agent_name(message)
        final_text = _extract_text(message).strip()
        cache = self._get_stream_cache()
        buffered = cache.pop(agent_name, []) if cache else []
        if buffered:
            buffered.append(final_text)
            combined = "\n".join(part for part in buffered if part)
        else:
            combined = final_text

        if not combined:
            return

        logger.info("[Fleet] Agent '%s' response: %s", agent_name, combined[:200])
        if ui := self._get_ui():
            ui.log_agent_message(
                AgentMessage(agent_name=agent_name, content=combined, mode="response")
            )

    async def plan_creation_callback(self, ledger: Any) -> None:
        """Log plan creation and facts gathered by the manager."""

        plan_lines = _coerce_lines(getattr(ledger, "plan", None))
        facts_lines = _coerce_lines(getattr(ledger, "facts", None))

        logger.info("[Fleet] Plan created:")
        for fact in facts_lines or ["(none)"]:
            logger.info("  Fact: %s", fact)
        for step in plan_lines or ["(none)"]:
            logger.info("  Step: %s", step)

        if ui := self._get_ui():
            ui.log_plan(facts_lines or ["(none)"], plan_lines or ["(none)"])

    async def progress_ledger_callback(self, ledger: Any) -> None:
        """Track progress evaluation and next actions."""

        is_satisfied = getattr(ledger, "is_request_satisfied", False)
        is_loop = getattr(ledger, "is_in_loop", False)
        next_speaker = getattr(ledger, "next_speaker", "unknown")
        instruction_lines = _coerce_lines(getattr(ledger, "instruction", None))

        logger.info("[Fleet] Progress evaluation:")
        logger.info("  Request satisfied: %s", is_satisfied)
        logger.info("  In loop: %s", is_loop)
        logger.info("  Next speaker: %s", next_speaker)
        if instruction_lines:
            for line in instruction_lines:
                logger.info("  Instruction: %s", line[:100])

        if ui := self._get_ui():
            status = (
                "Satisfied"
                if bool(is_satisfied)
                else ("Looping" if bool(is_loop) else "In progress")
            )
            instruction_text = "\n".join(instruction_lines) if instruction_lines else None
            ui.log_progress(status=status, next_speaker=next_speaker, instruction=instruction_text)

    async def notice_callback(self, message: str) -> None:
        """Display orchestration notices in the CLI."""

        if ui := self._get_ui():
            ui.log_notice(message)

    async def final_answer_callback(self, message: ChatMessage) -> None:
        """Log the final answer being returned to the user."""

        content = _extract_text(message)
        logger.info("[Fleet] Final answer: %s", content[:300])

        render_data = self._build_final_render_data(message, content)
        self._final_render.set(render_data)

        if ui := self._get_ui():
            ui.log_final(render_data)

    def consume_final_render(self) -> FinalRenderData | None:
        """Return and clear the most recent final render payload."""

        render = self._final_render.get()
        self._final_render.set(None)
        return render

    def _build_final_render_data(self, message: Any, content: str) -> FinalRenderData:
        sections: list[tuple[str, list[str]]] = []

        facts = _coerce_lines(_first_available(message, "facts", "facts_text"))
        if facts:
            sections.append(("Facts", facts))

        plan = _coerce_lines(_first_available(message, "plan", "plan_text"))
        if plan:
            sections.append(("Plan", plan))
            deliverable_lines: list[str] = []
            for index, line in enumerate(plan):
                if line.lower().startswith("deliverable"):
                    deliverable_lines = plan[index:]
                    break
            if deliverable_lines:
                sections.append(("Deliverable", deliverable_lines))

        status_value = _first_available(message, "state", "status")
        if status_value:
            sections.append(("Status", [str(status_value)]))

        result_lines = _coerce_lines(content)
        if result_lines:
            sections.append(("Result", result_lines))

        raw_output = content or getattr(message, "raw_text", "")
        return FinalRenderData(sections=sections or [("Result", ["(none)"])], raw_text=raw_output)


async def tool_call_callback(tool_name: str, tool_args: dict[str, Any], result: Any) -> None:
    """Log tool calls and results for debugging."""

    logger.debug("[Fleet] Tool call: %s", tool_name)
    logger.debug("  Args: %s", tool_args)
    logger.debug("  Result: %s", str(result)[:200])
