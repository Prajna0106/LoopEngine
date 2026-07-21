"""Security reviewer — checks for common security vulnerabilities."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound.review.base_reviewer import (
    BaseReviewer,
    IssueSeverity,
    ReviewIssue,
)


class SecurityReviewer(BaseReviewer):
    """Reviews code for security concerns."""

    @property
    def name(self) -> str:
        return "security"

    def _analyze(
        self,
        *,
        goal: str,  # noqa: ARG002
        artifacts: list[dict[str, Any]],
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        files = self._get_files(artifacts)

        for path, content in files.items():
            lines = content.splitlines()

            for i, line in enumerate(lines, 1):
                # Hard-coded secrets
                if re.search(
                    r"""(password|secret|api_key|token)\s*=\s*['"][^'"]+['"]""",
                    line,
                    re.IGNORECASE,
                ):
                    issues.append(
                        ReviewIssue(
                            message="Hard-coded secret or credential detected",
                            severity=IssueSeverity.CRITICAL,
                            file=path,
                            line=i,
                            category="secrets",
                            recommendation="Use environment variables or a secrets manager",
                            rule="hardcoded_secret",
                        )
                    )

                # SQL injection
                if re.search(
                    r"""(?:execute|cursor\.execute)\s*\(\s*['"].*%s""",
                    line,
                ):
                    issues.append(
                        ReviewIssue(
                            message="Possible SQL injection — string formatting in query",
                            severity=IssueSeverity.CRITICAL,
                            file=path,
                            line=i,
                            category="injection",
                            recommendation="Use parameterized queries",
                            rule="sql_injection",
                        )
                    )

                # eval/exec
                if re.search(r"\b(eval|exec)\s*\(", line):
                    issues.append(
                        ReviewIssue(
                            message="Use of eval/exec — potential code injection",
                            severity=IssueSeverity.HIGH,
                            file=path,
                            line=i,
                            category="injection",
                            recommendation="Avoid eval/exec; use safe alternatives",
                            rule="eval_exec",
                        )
                    )

                # Insecure random
                if re.search(r"\brandom\.(random|randint|choice)\b", line):
                    issues.append(
                        ReviewIssue(
                            message="Insecure random for potential security use",
                            severity=IssueSeverity.MEDIUM,
                            file=path,
                            line=i,
                            category="crypto",
                            recommendation="Use secrets module for cryptographic randomness",
                            rule="insecure_random",
                        )
                    )

                # Hardcoded IP/host
                if re.search(
                    r"""(?:host|host_name|ip_address)\s*=\s*['"]\d+\.\d+\.\d+\.\d+['"]""",
                    line,
                ):
                    issues.append(
                        ReviewIssue(
                            message="Hardcoded IP address or host",
                            severity=IssueSeverity.MEDIUM,
                            file=path,
                            line=i,
                            category="configuration",
                            recommendation="Use environment variables or config files",
                            rule="hardcoded_host",
                        )
                    )

        return issues

    def _recommendations(
        self,
        *,
        goal: str,  # noqa: ARG002
        artifacts: list[dict[str, Any]],  # noqa: ARG002
        issues: list[ReviewIssue],
    ) -> list[str]:
        recs: list[str] = []
        categories = {i.category for i in issues}
        if "secrets" in categories:
            recs.append("Never commit secrets — use environment variables or vaults")
        if "injection" in categories:
            recs.append("Sanitize all user inputs and use parameterized queries")
        if "crypto" in categories:
            recs.append("Use the secrets module for any security-sensitive randomness")
        return recs
