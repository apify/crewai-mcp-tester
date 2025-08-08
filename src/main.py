"""Main file of the Actor Inspector Agent for Apify Actors"""

from __future__ import annotations

import os

from apify import Actor
from crewai import Crew, Task
from pydantic import BaseModel, Field
from typing import Dict

from crewai import Agent
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

from crewai import LLM

from src.const import LLM_API_BASE_URL, LLM_MODEL, MCP_CONNECT_TIMEOUT

# Define the tool status structure
class ToolStatus(BaseModel):
    passed: bool = Field(description="Whether the tool test passed")
    detail: str = Field(description="Testing scenario description or explanation of failure")

# Define the structured output schema for LLM (excluding mcpUrl)
class MCPTestResult(BaseModel):
    allTestsPassed: bool = Field(description="Whether all MCP server tests passed")
    toolsStatus: Dict[str, ToolStatus] = Field(
        description="Status of each tool with passed boolean and detail string",
        default_factory=dict
    )


async def main() -> None:
    """Main entry point for the Apify Actor."""
    async with Actor:
        apify_token = os.getenv('APIFY_TOKEN', '')
        if not apify_token:
            raise ValueError("APIFY_TOKEN environment variable must be set for authentication.")

        llm = LLM(
            model=LLM_MODEL,
            temperature=0.0,
            api_base=LLM_API_BASE_URL,
            api_key="no-key-required-but-must-not-be-empty",
            extra_headers={
                "Authorization": f"Bearer {apify_token}",
            }
        )
        actor_input = await Actor.get_input() or {}
        mcp_url = actor_input.get('mcpUrl')
        headers = actor_input.get('headers', {})
        if not mcp_url:
            Actor.log.error('MCP URL is required in the input.')
            Actor.set_status_message('MCP URL is required in the input.')
            return


        # stdio MCP client
        args = [
            "mcp-remote",
            mcp_url,
        ]
        # Add headers if provided
        for key, value in headers.items():
            args.extend(["--header", f"{key}: {value}"])
        server_params=StdioServerParameters(
            command="npx",
            args=args
        )
        with MCPServerAdapter(server_params, connect_timeout=MCP_CONNECT_TIMEOUT) as mcp_tools:
            Actor.log.info(f"Available tools: {[tool.name for tool in mcp_tools]}")

            tool_agent = Agent(
                llm=llm,
                role="MCP tester agent",
                goal="Run a simple test on each available MCP server tool and provide a final verdict on whether the MCP server works correctly.",
                backstory="A seasoned MCP tester agent with extensive experience in testing MCP servers.",
                tools=mcp_tools,
                reasoning=False,
                verbose=False
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
                    - If rate limited, try again up to 3 times; if still rate limited, document the issue and consider it a failure.
                    - For each tool, record both whether it passed (true/false) and details:
                      - If passed: the detail should be the testing scenario description.
                      - If failed: the detail should explain why it failed.

                    Provide a comprehensive assessment of the MCP server's functionality.
                    
                    You must return your results in the exact format specified by the output schema.

                    You must test only the tools listed below and nothing else: {", ".join([tool.name for tool in mcp_tools])}
                """,
                expected_output="""
                    A structured test result containing:
                    - allTestsPassed: Boolean indicating overall success or failure.
                    - toolsStatus: Dictionary mapping each tool name to an object with:
                      - passed: Boolean (true if working, false if not).
                      - detail: String (testing scenario description, or explanation of failure).
                """,
                agent=tool_agent,
                output_pydantic=MCPTestResult
            )

            crew = Crew(
                agents=[tool_agent],
                tasks=[task],
                verbose=True
            )
            result = crew.kickoff()
            input_tokens = result.token_usage.prompt_tokens
            output_tokens = result.token_usage.completion_tokens
            total_tokens = input_tokens + output_tokens
            Actor.log.info(f"Input tokens: {input_tokens}, Output tokens: {output_tokens}, Total tokens: {total_tokens}")
 
            # Access structured output
            if hasattr(result, 'pydantic') and result.pydantic:
                structured_result = result.pydantic
                Actor.log.info(f"All tests passed: {structured_result.allTestsPassed}")
                Actor.log.info(f"Tools Status: {structured_result.toolsStatus}")

                # Deserialize toolsStatus from ToolStatus objects to dictionaries
                tools_status_dict = {}
                for tool_name, tool_status in structured_result.toolsStatus.items():
                    tools_status_dict[tool_name] = tool_status.dict()

                # Save structured data to Apify dataset
                await Actor.push_data({
                    "mcpUrl": mcp_url,
                    "allTestsPassed": structured_result.allTestsPassed,
                    "toolsStatus": tools_status_dict
                })
            else:
                # Fallback to raw output if structured parsing fails
                Actor.log.warning("Structured output not available, using raw result:")
                Actor.log.warning(f"Raw result: {result}")
