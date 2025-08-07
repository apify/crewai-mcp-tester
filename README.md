# MCP Server Tester

Automated testing tool for Model Context Protocol (MCP) servers. Tests available tools and generates reports on functionality and reliability.

## Features

- Connects to MCP servers via URL and tests all available tools
- Uses GPT-4.1 Mini to interact with MCP tools and evaluate responses
- Generates test reports with pass/fail status and findings
- Supports custom headers for authentication
- Token-based pricing model using [Pay per Event](https://docs.apify.com/sdk/js/docs/guides/pay-per-event)
- Runs on Apify platform

## Output Data

| Field | Type | Description |
|-------|------|-------------|
| `mcpUrl` | String | The tested MCP server URL |
| `worksCorrectly` | Boolean | Overall pass/fail status of the MCP server |
| `report` | String | Detailed test report with findings, errors, and recommendations |

## Usage

1. Navigate to the Actor page
2. Provide the MCP server URL
3. Add authentication headers if required
4. Start the test
5. Review the generated report

## Pricing

Token-based pricing:

- Input tokens: $0.00048 per 1,000 tokens
- Output tokens: $0.00192 per 1,000 tokens

Charges based on actual AI token consumption.

## Input

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

## Output

The Actor returns structured data in JSON format:

```json
{
  "mcpUrl": "https://mcp.apify.com",
  "worksCorrectly": true,
  "report": "Testing of MCP server tools was conducted as follows..."
}
```

## Configuration

### Custom Headers
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
