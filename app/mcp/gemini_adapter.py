"""Dynamic adapter converting MCP server tool catalogs into Gemini-compatible callables."""

import inspect
import json
from collections.abc import Callable
from typing import Any

import anyio
from mcp.server import MCPServer


def adapt_mcp_server_to_gemini_tools(server: MCPServer) -> list[Callable[..., Any]]:
    """Dynamically discover all tools exposed by an MCPServer and adapt them for Google GenAI.

    Each discovered tool preserves its original signature, docstring, and type annotations,
    while guaranteeing that execution is routed strictly through the MCP protocol (`server.call_tool`).

    Args:
        server: The running or registered MCPServer instance.

    Returns:
        List of callable functions ready to be passed to Gemini's `tools=[...]` configuration.
    """
    tools = anyio.run(server.list_tools)
    gemini_callables: list[Callable[..., Any]] = []

    for tool_def in tools:
        tool_name = tool_def.name
        tool_desc = tool_def.description or ""
        tool_entry = server._tool_manager.get_tool(tool_name)
        original_fn = tool_entry.fn

        def _create_mcp_invoker(name: str, desc: str, orig_fn: Callable[..., Any]):
            def mcp_dynamic_tool(*args, **kwargs):
                sig = inspect.signature(orig_fn)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()

                import time

                t0 = time.perf_counter()

                async def _call():
                    res = await server.call_tool(name=name, arguments=bound.arguments)
                    return [json.loads(c.text) for c in res.content if hasattr(c, "text")]

                data = anyio.run(_call)
                tool_duration = round(time.perf_counter() - t0, 3)

                # Store span in current thread/context if callback exists
                if hasattr(mcp_dynamic_tool, "on_span_recorded") and callable(mcp_dynamic_tool.on_span_recorded):
                    mcp_dynamic_tool.on_span_recorded(
                        name=f"mcp.tool.{name}",
                        duration=tool_duration,
                        attributes={"tool_name": name, "city": bound.arguments.get("city", "")},
                    )

                return data

            mcp_dynamic_tool.__name__ = name
            mcp_dynamic_tool.__doc__ = desc
            mcp_dynamic_tool.__signature__ = inspect.signature(orig_fn)
            return mcp_dynamic_tool

        gemini_callables.append(_create_mcp_invoker(tool_name, tool_desc, original_fn))

    return gemini_callables
