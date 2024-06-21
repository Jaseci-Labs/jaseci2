"""Core constructs for Jac Language."""

from __future__ import annotations

import unittest
from contextvars import ContextVar
from typing import Any, Callable, Optional, TypedDict, Union
from uuid import UUID

from .architype import NodeAnchor, Root
from .memory import ShelfMemory


EXECUTION_CONTEXT = ContextVar[Optional["ExecutionContext"]]("ExecutionContext")


class ContextOptions(TypedDict, total=False):
    """Execution Context Options."""

    root: Optional[NodeAnchor]
    entry: Optional[NodeAnchor]


class ExecutionContext:
    """Execution Context."""

    def __init__(
        self,
        session: Optional[str] = "",
        root: Optional[NodeAnchor] = None,
        entry: Optional[NodeAnchor] = None,
    ) -> None:
        """Create JacContext."""
        self.datasource: ShelfMemory = ShelfMemory(session)
        self.reports: list[Any] = []
        self.super_root = self.load(
            NodeAnchor(id=UUID(int=0)), self.generate_super_root
        )
        self.root: NodeAnchor = self.load(root, self.super_root)
        self.entry: NodeAnchor = self.load(entry, self.root)

    def generate_super_root(self) -> NodeAnchor:
        """Generate default super root."""
        super_root = NodeAnchor(id=UUID(int=0), current_access_level=1)
        architype = super_root.architype = object.__new__(Root)
        architype._jac_ = super_root
        self.datasource.set(super_root, True)
        return super_root

    def load(
        self,
        anchor: Optional[NodeAnchor],
        default: Union[NodeAnchor, Callable[[], NodeAnchor]],
    ) -> NodeAnchor:
        """Load initial anchors."""
        if anchor and (_anchor := self.datasource.find_one(anchor.id)):
            anchor.__dict__.update(_anchor.__dict__)
            anchor.current_access_level = 1
        else:
            anchor = default() if callable(default) else default

        return anchor

    def close(self) -> None:
        """Clean up context."""
        self.datasource.close()

    @staticmethod
    def get(
        session: Optional[str] = "", options: Optional[ContextOptions] = None
    ) -> ExecutionContext:
        """Get or create execution context."""
        if not isinstance(ctx := EXECUTION_CONTEXT.get(None), ExecutionContext):
            EXECUTION_CONTEXT.set(ctx := ExecutionContext(session, **options or {}))
        return ctx


class JacTestResult(unittest.TextTestResult):
    """Jac test result class."""

    def __init__(
        self,
        stream,  # noqa
        descriptions,  # noqa
        verbosity: int,
        max_failures: Optional[int] = None,
    ) -> None:
        """Initialize FailFastTestResult object."""
        super().__init__(stream, descriptions, verbosity)  # noqa
        self.failures_count = JacTestCheck.failcount
        self.max_failures = max_failures

    def addFailure(self, test, err) -> None:  # noqa
        """Count failures and stop."""
        super().addFailure(test, err)
        self.failures_count += 1
        if self.max_failures is not None and self.failures_count >= self.max_failures:
            self.stop()

    def stop(self) -> None:
        """Stop the test execution."""
        self.shouldStop = True


class JacTextTestRunner(unittest.TextTestRunner):
    """Jac test runner class."""

    def __init__(self, max_failures: Optional[int] = None, **kwargs) -> None:  # noqa
        """Initialize JacTextTestRunner object."""
        self.max_failures = max_failures
        super().__init__(**kwargs)

    def _makeResult(self) -> JacTestResult:  # noqa
        """Override the method to return an instance of JacTestResult."""
        return JacTestResult(
            self.stream,
            self.descriptions,
            self.verbosity,
            max_failures=self.max_failures,
        )


class JacTestCheck:
    """Jac Testing and Checking."""

    test_case = unittest.TestCase()
    test_suite = unittest.TestSuite()
    breaker = False
    failcount = 0

    @staticmethod
    def reset() -> None:
        """Clear the test suite."""
        JacTestCheck.test_case = unittest.TestCase()
        JacTestCheck.test_suite = unittest.TestSuite()

    @staticmethod
    def run_test(xit: bool, maxfail: int | None, verbose: bool) -> None:
        """Run the test suite."""
        verb = 2 if verbose else 1
        runner = JacTextTestRunner(max_failures=maxfail, failfast=xit, verbosity=verb)
        result = runner.run(JacTestCheck.test_suite)
        if result.wasSuccessful():
            print("Passed successfully.")
        else:
            fails = len(result.failures)
            JacTestCheck.failcount += fails
            JacTestCheck.breaker = (
                (JacTestCheck.failcount >= maxfail) if maxfail else True
            )

    @staticmethod
    def add_test(test_fun: Callable) -> None:
        """Create a new test."""
        JacTestCheck.test_suite.addTest(unittest.FunctionTestCase(test_fun))

    def __getattr__(self, name: str) -> object:
        """Make convenient check.Equal(...) etc."""
        return getattr(JacTestCheck.test_case, name)
