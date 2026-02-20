"""
Eval runner: runs the agent on each case and checks routing + tool usage.
"""

from collections.abc import Callable

from evals.dataset import get_eval_cases
from evals.schemas import AgentRunResult, EvalCase, EvalResult, ToolCallRecord


def _check_case(case: EvalCase, run: AgentRunResult) -> EvalResult:
    """Evaluate one agent run against the case criteria."""
    failures: list[str] = []
    actual_tool_names = [t.name for t in run.tool_calls]

    # 1. Route must match
    if run.route != case.expected_route:
        failures.append(f"route: expected '{case.expected_route}', got '{run.route}'")

    # 2. At least one of expected_tools_any must be called (if any specified)
    if case.expected_tools_any:
        if not any(t in actual_tool_names for t in case.expected_tools_any):
            failures.append(
                f"tools: expected at least one of {case.expected_tools_any}, "
                f"got {actual_tool_names}"
            )

    # 3. None of forbidden_tools must be called
    called_forbidden = [t for t in case.forbidden_tools if t in actual_tool_names]
    if called_forbidden:
        failures.append(f"forbidden tools called: {called_forbidden}")

    passed = len(failures) == 0
    details = case.description
    if failures:
        details += "; " + "; ".join(failures)

    return EvalResult(
        case_id=case.id,
        passed=passed,
        details=details,
        actual_route=run.route,
        actual_tool_names=actual_tool_names,
        failures=failures,
    )


def run_evals(
    agent_runner: Callable[[str], AgentRunResult],
    *,
    case_ids: list[str] | None = None,
) -> list[EvalResult]:
    """
    Run all (or selected) eval cases and return results.

    Args:
        agent_runner: Callable that takes (user_message: str) and returns
                      an AgentRunResult (route + tool_calls).
        case_ids: If set, only run these case ids (e.g. ["money_problems"]).
                  If None, run all cases.

    Returns:
        List of EvalResult, one per case.
    """
    cases = get_eval_cases()
    if case_ids is not None:
        cases = [c for c in cases if c.id in case_ids]

    results: list[EvalResult] = []
    for case in cases:
        run_result = agent_runner(case.user_message)
        if not isinstance(run_result, AgentRunResult):
            # Allow dict for flexibility; convert to AgentRunResult
            if isinstance(run_result, dict):
                run_result = AgentRunResult(
                    route=run_result.get("route", ""),
                    tool_calls=[
                        ToolCallRecord(name=t.get("name", ""), args=t.get("args", {}))
                        for t in run_result.get("tool_calls", [])
                    ],
                )
            else:
                results.append(
                    EvalResult(
                        case_id=case.id,
                        passed=False,
                        details=f"agent_runner did not return AgentRunResult: {type(run_result)}",
                        failures=["invalid result type"],
                    )
                )
                continue
        results.append(_check_case(case, run_result))

    return results
