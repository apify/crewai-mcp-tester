"""Main file of the Actor Inspector Agent for Apify Actors"""

from __future__ import annotations

import os

from apify import Actor
from crewai import LLM, Agent, Crew, Task
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
from pydantic import BaseModel, Field

from src.const import LLM_API_BASE_URL, LLM_MODEL, MCP_CONNECT_TIMEOUT


# Define the tool status structure
class ToolStatus(BaseModel):
    name: str = Field(description='Name of the tool')
    passed: bool = Field(description='Whether the tool test passed')
    detail: str = Field(description='Testing scenario description or explanation of failure')


# Define the structured output schema for LLM (excluding mcpUrl)
class MCPTestResult(BaseModel):
    tools_status: list[ToolStatus]
    all_tests_passed: bool = Field(description='Overall pass/fail status of all MCP server tests')


def print_test_results(tools_status: list[ToolStatus]) -> None:
    """Print individual test results and return overall status and summary."""
    passed_count = 0
    failed_count = 0

    Actor.log.info('=== Test results ===')
    for tool in tools_status:
        if tool.passed:
            passed_count += 1
            Actor.log.info(f'✔ {tool.name}: PASSED - {tool.detail}')
        else:
            failed_count += 1
            Actor.log.info(f'✖ {tool.name}: FAILED - {tool.detail}')

    all_passed = failed_count == 0
    total = len(tools_status)

    Actor.log.info('=== Summary ===')
    Actor.log.info(f'Total: {total} | Passed: {passed_count} | Failed: {failed_count}')
    Actor.log.info(f'All tests passed: {all_passed}')


async def main() -> None:
    """Main entry point for the Apify Actor."""
    async with Actor:
        apify_token = os.getenv('APIFY_TOKEN', '')
        if not apify_token:
            raise ValueError('APIFY_TOKEN environment variable must be set for authentication.')

        llm = LLM(
            model=LLM_MODEL,
            temperature=0.0,
            api_base=LLM_API_BASE_URL,
            api_key='no-key-required-but-must-not-be-empty',
            extra_headers={
                'Authorization': f'Bearer {apify_token}',
            },
        )
        actor_input = await Actor.get_input() or {}
        mcp_url = actor_input.get('mcpUrl')
        headers = actor_input.get('headers', {})
        if not mcp_url:
            msg = 'You need to provide the MCP URL in the input as "mcpUrl".'
            Actor.log.error(msg)
            await Actor.set_status_message(msg)
            return

        # stdio MCP client
        args = [
            'mcp-remote',
            mcp_url,
        ]
        # Add headers if provided
        for key, value in headers.items():
            args.extend(['--header', f'{key}: {value}'])
        server_params = StdioServerParameters(command='npx', args=args)
        with MCPServerAdapter(server_params, connect_timeout=MCP_CONNECT_TIMEOUT) as mcp_tools:
            Actor.log.info(f'Available tools: {[tool.name for tool in mcp_tools]}')

            tool_agent = Agent(
                llm=llm,
                role='MCP tester agent',
                goal='Run test on each available MCP server tool and provide a final verdict '
                'on whether the MCP server works correctly.',
                backstory='A seasoned MCP tester agent with extensive experience in testing MCP servers.',
                tools=mcp_tools,
                reasoning=False,
                verbose=False,
            )

            task = Task(
                description=f"""
                    Test the MCP server and its available tools.

                    For each available MCP server tool:
                    1. Run a basic operation to test its functionality.
                    2. Verify that each tool responds correctly and as expected.
                    3. Document any errors or unexpected behavior.
                    4. Record the status of each tool individually with detailed results.

                    Requirements to pass:
                    - All tools must respond correctly without errors.
                    - If you think one tools depends on another tool, test the dependent tool later.
                    - If rate limited, try again 3 times; if still rate limited, document the issue, mark it as failure.
                    - For each tool, record both whether it passed (true/false) and details:
                      - If passed: the detail should be the testing scenario description.
                      - If failed: the detail should explain why it failed.

                    Provide a comprehensive assessment of the MCP server's functionality.
                    You must return your results in the exact format specified by the output schema.

                    You must test only the tools listed below and nothing else:
                    {', '.join([tool.name for tool in mcp_tools])}
                """,
                expected_output="""
                    A structured test result containing:
                    - toolsStatus: List of tool status objects, each with:
                      - name: String (tool name).
                      - passed: Boolean (true if working, false if not).
                      - detail: String (testing scenario description, or explanation of failure).
                    - allTestsPassed: Boolean (true if ALL tools passed, false if ANY tool failed).
                """,
                agent=tool_agent,
                output_pydantic=MCPTestResult,
            )

            crew = Crew(agents=[tool_agent], tasks=[task], verbose=True)
            result = crew.kickoff()
            input_tokens = result.token_usage.prompt_tokens
            output_tokens = result.token_usage.completion_tokens
            total_tokens = input_tokens + output_tokens
            Actor.log.info(
                f'Input tokens: {input_tokens}, Output tokens: {output_tokens}, Total tokens: {total_tokens}'
            )

            # Process structured output
            if hasattr(result, 'pydantic') and result.pydantic:
                structured_result = result.pydantic

                # Print results and get summary
                print_test_results(structured_result.tools_status)

                results = []
                for tool in structured_result.tools_status:
                    results.append(tool.model_dump())  # noqa: PERF401 (comprehension does not work here)

                # Save to Apify dataset
                await Actor.push_data(results)
            else:
                # Fallback to raw output if structured parsing fails
                Actor.log.warning('Structured output not available, using raw result:')
                Actor.log.warning(f'Raw result: {result}')
