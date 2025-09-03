# CrewAI MCP tester

It is important to ensure that your MCP server is functioning correctly and that all tools are available and working as expected. This Actor automates the manual testing process and provides a detailed report on the status of each tool.

Since MCP servers are often used in agentic-based applications, it is essential to test the MCP server using an agentic approach.

> **ℹ️ Notice:**  
> This Actor internally uses the [Apify Openrouter Actor](https://apify.com/apify/openrouter) to call an LLM. You will be billed for LLM usage through this Actor.

## 🔥 Features

- Connects to MCP servers via URL and tests all available tools
- Uses GPT-4.1 Mini to interact with MCP tools and evaluate responses
- Generates test reports with pass/fail status and findings
- Supports custom headers for authentication
- Token-based pricing model using [Pay per Event](https://docs.apify.com/sdk/js/docs/guides/pay-per-event)
- Runs on Apify platform

## 📊 Output data

The Actor returns individual records for each tool tested. Each record contains:

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Name of the MCP tool that was tested |
| `passed` | Boolean | Whether the tool test passed (true/false) |
| `detail` | String | Testing scenario description or explanation of failure |

## 🚀 Usage

1. Navigate to the Actor page
2. Provide the MCP server URL
3. Add authentication headers for the MCP server (if required)
4. Start the test
5. Review the generated report

## 💰 Pricing

You will be charged based on LLM token usage. For a simple MCP server with a few tools, the cost should be under $0.05 per test run.

## 💾 Input

The Actor accepts the following input parameters:

```json
{
  "mcpUrl": "https://your-mcp-server.com/mcp",
  "headers": {
    "Authorization": "Bearer your-token",
    "X-Custom-Header": "custom-value"
  }
}
```

**Parameters:**
- `mcpUrl` (required): MCP server endpoint URL
- `headers` (optional): HTTP headers for authentication or configuration

## 🔢 Output

The Actor returns individual records for each tool tested. Each record is a separate JSON object:

```json
[
  {
    "name": "get-actor-details",
    "passed": true,
    "detail": "Successfully retrieved detailed information about the actor 'apify/proxy-test'."
  },
  {
    "name": "search-actors",
    "passed": true,
    "detail": "Successfully searched for actors with the keyword 'test' and received valid results."
  },
  {
    "name": "search-apify-docs",
    "passed": true,
    "detail": "Successfully searched Apify documentation for the keyword 'test' and received relevant documentation links."
  },
  {
    "name": "fetch-apify-docs",
    "passed": true,
    "detail": "Successfully fetched full content of an Apify documentation page about automated testing."
  },
  {
    "name": "add-actor",
    "passed": true,
    "detail": "Successfully added the actor 'apify/proxy-test' to the available tools."
  },
  {
    "name": "apify-slash-rag-web-browser",
    "passed": true,
    "detail": "Successfully ran a basic operation querying 'san francisco weather' and received results without errors."
  }
]
```

## 🔧 Configuration

### Custom headers
For MCP servers requiring authentication:

```json
{
  "mcpUrl": "https://secure-mcp-server.com/mcp",
  "headers": {
    "Authorization": "Bearer your-secure-token",
    "X-API-Key": "your-api-key",
  }
}
```

## 🌐 Open source

This Actor is open source and available on [GitHub](https://github.com/apify/crewai-mcp-tester).

## 📚 Resources

- [Apify Actor CrewAI template](https://apify.com/templates/python-crewai)
- [How to Build an AI Agent with CrewAI](https://blog.apify.com/how-to-build-an-ai-agent/)
- [How to use MCP with Apify Actors](https://blog.apify.com/how-to-use-mcp/)
- [Webinar: Building and monetizing MCP servers on Apify](https://www.youtube.com/watch?v=w3AH3jIrXXo)
