"""Main file of the Actor Inspector Agent for Apify Actors"""

from __future__ import annotations

from apify import Actor
from crewai import Crew, Task
from pydantic import BaseModel, Field

from crewai import Agent
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

from crewai import LLM

from src.const import LLM_MODEL, MCP_CONNECT_TIMEOUT
from .billing import charge_tokens

# Define the structured output schema for LLM (excluding mcpUrl)
class MCPTestResult(BaseModel):
    worksCorrectly: bool = Field(description="Whether the MCP server works correctly")
    report: str = Field(description="Detailed test report with findings")

llm = LLM(
    model=LLM_MODEL,
    temperature=0.0,
)

async def main() -> None:
    """Main entry point for the Apify Actor."""
    async with Actor:
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
                reasoning=True,
                verbose=True
            )

            task = Task(
                description=f"""
                    Test the MCP server and its available tools.
                    
                    For each available MCP server tool:
                    1. Run a basic operation to test functionality
                    2. Verify that each tool responds correctly and as expected
                    3. Document any errors or unexpected behavior
                    
                    Provide a comprehensive assessment of the MCP server's functionality.
                    
                    You must return your results in the exact format specified by the output schema.
                """,
                expected_output="""
                    A structured test result containing:
                    - worksCorrectly: Boolean indicating overall success/failure
                    - report: Detailed summary of all tests performed, results, and final verdict
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

            # Charge for token usage
            try:
                await charge_tokens(input_tokens, output_tokens)
                Actor.log.info("Successfully charged for token usage")
            except Exception as e:
                Actor.log.error(f"Failed to charge for tokens: {e}")
                # Don't fail the entire run if charging fails
            
            # Access structured output
            if hasattr(result, 'pydantic') and result.pydantic:
                structured_result = result.pydantic
                Actor.log.info(f"MCP works Correctly: {structured_result.worksCorrectly}")
                Actor.log.info(f"Report: {structured_result.report}")

                # Save structured data to Apify dataset
                await Actor.push_data({
                    "mcpUrl": mcp_url,
                    "worksCorrectly": structured_result.worksCorrectly,
                    "report": structured_result.report
                })
            else:
                # Fallback to raw output if structured parsing fails
                Actor.log.warning("Structured output not available, using raw result:")
                Actor.log.warning(f"Raw result: {result}")
