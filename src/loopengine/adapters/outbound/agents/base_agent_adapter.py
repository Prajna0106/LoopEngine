"""Base agent adapter — common infrastructure for CLI-based agents.

Provides process execution, streaming output, timeout, retry, error
handling, and structured logging.  Concrete adapters only need to
define the CLI command and argument formatting.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from loopengine.adapters.outbound._subprocess_utils import base_env, is_command_available
from loopengine.core.domain.exceptions.agent_exceptions import (
    AgentError,
    AgentRefusedError,
    AgentTimeoutError,
)
from loopengine.core.ports.outbound.agent_port import AgentResponse, BaseAgent

log = structlog.get_logger()


# ── Configuration ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class ProcessConfig:
    """Tuning knobs for subprocess execution."""

    timeout: float = 120.0
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)


# ── Base adapter ───────────────────────────────────────────────────────


class BaseAgentAdapter(BaseAgent):
    """Abstract adapter that executes agents as CLI subprocesses.

    Subclasses override:
    * ``command``  — the CLI executable (e.g. ``["claude", "-p"]``).
    * ``build_args`` — turn a prompt + context into CLI arguments.
    * ``parse_response`` — extract structured output from stdout.
    * ``is_available`` — check whether the CLI is installed / configured.
    """

    def __init__(self, *, model: str = "", config: ProcessConfig | None = None) -> None:
        self._config = config or ProcessConfig()
        self._model = model

    # ── Subclass hooks ────────────────────────────────────────────────

    @property
    def name(self) -> str:
        """Human-readable agent identifier.

        Override in subclasses.
        """
        raise NotImplementedError

    @property
    def model(self) -> str:
        """Model identifier (e.g. 'claude-sonnet-4-20250514')."""
        return self._model

    @property
    def command(self) -> list[str]:
        """The base CLI command (e.g. ``["claude", "-p"]``).

        Override in subclasses.  The prompt is appended by default;
        override ``build_args`` for full control.
        """
        raise NotImplementedError

    def build_args(
        self,
        prompt: str,
        *,
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> list[str]:
        """Build the full argument list for the subprocess.

        The default implementation returns ``self.command + [prompt]``.
        """
        return [*self.command, prompt]

    def parse_response(self, stdout: str, stderr: str) -> AgentResponse:
        """Parse raw subprocess output into an ``AgentResponse``.

        Override to extract structured data (model name, usage, etc.).
        """
        return AgentResponse(
            content=stdout.strip(),
            model=self._model,
            metadata={"agent": self.name, "stderr": stderr.strip()},
        )

    def format_timeout_message(self, timeout: float) -> str:
        """Human-readable timeout error message."""
        return f"Agent {self.name!r} timed out after {timeout}s"

    # ── Core invocation ───────────────────────────────────────────────

    def invoke(
        self,
        prompt: str,
        *,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> AgentResponse:
        """Execute the agent CLI with retry logic and timeout."""
        effective_timeout = timeout or self._config.timeout
        last_error: Exception | None = None

        for attempt in range(1, self._config.max_retries + 1):
            try:
                return self._execute(prompt, context=context, timeout=effective_timeout)
            except AgentTimeoutError:
                raise  # timeouts are never retried
            except AgentError:
                raise  # explicit agent errors are not retried
            except Exception as exc:
                last_error = exc
                if attempt < self._config.max_retries:
                    delay = self._config.retry_delay * (
                        self._config.retry_backoff ** (attempt - 1)
                    )
                    log.warning(
                        "agent_retry",
                        agent=self.name,
                        attempt=attempt,
                        max_retries=self._config.max_retries,
                        delay=delay,
                        error=str(exc),
                    )
                    time.sleep(delay)

        raise AgentError(
            f"Agent {self.name!r} failed after {self._config.max_retries} attempts",
            agent=self.name,
        ) from last_error

    def _execute(
        self,
        prompt: str,
        *,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> AgentResponse:
        """Single execution attempt — no retry."""
        args = self.build_args(prompt, context=context)
        effective_timeout = timeout or self._config.timeout

        log.debug(
            "agent_invoke",
            agent=self.name,
            command=args[0] if args else "",
            timeout=effective_timeout,
        )

        merged_env = {**base_env(), **self._config.env}

        resolved = args[0] if args else ""
        if resolved:
            found = shutil.which(resolved, path=merged_env.get("PATH"))
            if found:
                args = [found, *args[1:]]

        try:
            result = subprocess.run(  # noqa: S603
                args,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=self._config.cwd,
                env=merged_env,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AgentTimeoutError(self.name, effective_timeout) from exc
        except FileNotFoundError as exc:
            raise AgentRefusedError(
                self.name,
                reason=f"CLI not found: {args[0]!r}",
            ) from exc
        except OSError as exc:
            raise AgentError(
                f"Failed to execute {args[0]!r}: {exc}",
                agent=self.name,
            ) from exc

        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise AgentRefusedError(
                self.name,
                reason=stderr or f"exit code {result.returncode}",
            )

        return self.parse_response(result.stdout, result.stderr)

    # ── Streaming invocation ──────────────────────────────────────────

    def invoke_streaming(
        self,
        prompt: str,
        *,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> subprocess.Popen[str]:
        """Start the agent as a streaming subprocess.

        Returns a ``Popen`` object the caller must iterate and close.
        Raises ``AgentTimeoutError`` if the process does not start within
        the timeout.
        """
        args = self.build_args(prompt, context=context)
        effective_timeout = timeout or self._config.timeout
        merged_env = {**base_env(), **self._config.env}

        log.debug(
            "agent_invoke_streaming",
            agent=self.name,
            command=args[0] if args else "",
            timeout=effective_timeout,
        )

        try:
            proc = subprocess.Popen(  # noqa: S603
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self._config.cwd,
                env=merged_env,
            )
        except FileNotFoundError as exc:
            raise AgentRefusedError(
                self.name,
                reason=f"CLI not found: {args[0]!r}",
            ) from exc
        except OSError as exc:
            raise AgentError(
                f"Failed to start {args[0]!r}: {exc}",
                agent=self.name,
            ) from exc

        return proc

    # ── Availability ──────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Check whether the CLI binary exists on PATH."""
        return is_command_available(self.command)


# ── Helpers ────────────────────────────────────────────────────────────
