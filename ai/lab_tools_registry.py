#!/usr/bin/env python3

from .lab_tools import get_lab_status
from .tool_registry import register


def register_system_tools():
    register(
        name="get_lab_status",
        description=(
            "Return current RichardLab system resources, module states, "
            "experiment/report activity, and latest report."
        ),
        function=get_lab_status,
        category="system",
        safety="read_only",
    )


def load_registry():
    register_system_tools()

    from .hive.workers.experiments import register_tools
    register_tools()

    from .hive.workers.time_ledger import register_tools as register_time_tools
    register_time_tools()

    return True
