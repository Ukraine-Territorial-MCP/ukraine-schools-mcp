"""Integration test for Ukraine Schools MCP."""

import asyncio
import json
import os
import socket
import subprocess
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

PORT = 18916
URL = f"http://127.0.0.1:{PORT}/mcp"


def decode_result(result):
    if result.is_error:
        raise RuntimeError(str(result.content))

    data = getattr(result, "structured_content", None)

    if data:
        return data

    for item in result.content:
        if hasattr(item, "text"):
            return json.loads(item.text)

    raise RuntimeError("No JSON returned")


async def main():
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1", PORT)) == 0:
            raise RuntimeError("Test port already in use")

    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "schools_server:app",
            "--host", "127.0.0.1",
            "--port", str(PORT),
            "--log-level", "error",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    try:
        for _ in range(75):
            if process.poll() is not None:
                raise RuntimeError(
                    process.stderr.read().decode()[-2000:]
                )

            with socket.socket() as sock:
                if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                    break

            await asyncio.sleep(0.2)
        else:
            raise RuntimeError("Server startup timeout")

        async with streamable_http_client(URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                available = await session.list_tools()
                names = [t.name for t in available.tools]

                print("=== MCP TOOLS ===")
                print(names)

                expected = {
                    "get_school_info",
                    "list_schools_by_community",
                    "get_education_budget",
                }
                assert expected.issubset(names)

                print("\n=== 1. SCHOOL ===")
                school = decode_result(
                    await session.call_tool(
                        "get_school_info",
                        {"school_id": 146644},
                    )
                )
                assert school["found"]
                assert school["territory"]["found"]
                print("School:", school["name"])
                print("RESULT: SUCCESS")

                print("\n=== 2. COMMUNITY ===")
                community = decode_result(
                    await session.call_tool(
                        "list_schools_by_community",
                        {
                            "community_code":
                            "UA74100110000030364"
                        },
                    )
                )
                assert community["count"] == 5
                print("Community:", community["community_name"])
                print("Schools:", community["count"])
                print("RESULT: SUCCESS")

                print("\n=== 3. EDUCATION BUDGET ===")
                budget = decode_result(
                    await session.call_tool(
                        "get_education_budget",
                        {
                            "budget_code": "2551500000",
                            "year": 2026,
                        },
                    )
                )
                assert len(budget["programs"]) == 3
                assert budget["period"]
                print("Period:", budget["period"])
                print("Programs:", len(budget["programs"]))
                print("Actual:", budget["total_actual"], "UAH")
                print("RESULT: SUCCESS")

        print("\n=== ALL THREE MCP TOOLS: SUCCESS ===")

    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        print("Test server stopped")


asyncio.run(main())
