#!/usr/bin/env python3
"""
Mem0 Antigravity MCP Server (Pure Python Standard Library)
Zero external dependencies required on the host.
Communicates with Antigravity via MCP JSON-RPC 2.0 over stdio,
and connects to the local Docker Mem0 server at http://localhost:28842.
"""

import sys
import json
import os
import urllib.request
import urllib.parse
import urllib.error

MEM0_SERVER_URL = os.getenv("MEM0_SERVER_URL", "http://localhost:28842").rstrip("/")

TOOLS = [
    {
        "name": "mem0_search_memory",
        "description": "Semantic search across long-term cross-conversation memories in the local Mem0 vector database. Use to recall project guidelines, architecture decisions, user preferences, facts, and past context.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query or concept to look up in memory"
                },
                "project": {
                    "type": "string",
                    "description": "Filter by project name (e.g. 'fieldnation', 'personal', 'general', or 'all')",
                    "default": "all"
                },
                "category": {
                    "type": "string",
                    "description": "Filter by category ('architecture', 'guideline', 'preference', 'decision', 'fact', or 'all')",
                    "default": "all"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of memories to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "mem0_add_memory",
        "description": "Persist an important insight, project guideline, user preference, architectural decision, or fact to long-term memory across conversations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The memory text or context to save"
                },
                "project": {
                    "type": "string",
                    "description": "Project identifier (e.g. 'fieldnation', 'general', 'personal')",
                    "default": "general"
                },
                "category": {
                    "type": "string",
                    "description": "Category ('architecture', 'guideline', 'preference', 'decision', 'fact', 'general')",
                    "default": "guideline"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tags (e.g. ['php8', 'service-locator', 'mcp'])",
                    "default": []
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional custom key-value metadata object",
                    "default": {}
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "mem0_list_memories",
        "description": "List recent memories in chronological order with optional project or category filters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Filter by project name ('fieldnation', 'general', etc. or 'all')",
                    "default": "all"
                },
                "category": {
                    "type": "string",
                    "description": "Filter by category ('architecture', 'guideline', 'preference', 'decision', 'fact', or 'all')",
                    "default": "all"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default: 15)",
                    "default": 15
                }
            }
        }
    },
    {
        "name": "mem0_get_memory",
        "description": "Retrieve full details, metadata, and edit history for a specific memory UUID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "string",
                    "description": "The UUID of the memory to fetch"
                }
            },
            "required": ["memory_id"]
        }
    },
    {
        "name": "mem0_update_memory",
        "description": "Update or refine an existing memory's content, project, category, or tags.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "string",
                    "description": "The UUID of the memory to update"
                },
                "content": {
                    "type": "string",
                    "description": "New memory text content"
                },
                "project": {
                    "type": "string",
                    "description": "New project name"
                },
                "category": {
                    "type": "string",
                    "description": "New category"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "New list of tags"
                }
            },
            "required": ["memory_id"]
        }
    },
    {
        "name": "mem0_delete_memory",
        "description": "Delete an obsolete or incorrect memory from the local vector database.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "string",
                    "description": "The UUID of the memory to delete"
                }
            },
            "required": ["memory_id"]
        }
    },
    {
        "name": "mem0_get_stats",
        "description": "Get metrics and health status of the local Mem0 memory server.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


def http_request(method: str, path: str, data: dict = None, params: dict = None) -> dict:
    url = f"{MEM0_SERVER_URL}{path}"
    if params:
        query_string = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        if query_string:
            url = f"{url}?{query_string}"

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            content = resp.read().decode("utf-8")
            return {"status": resp.status, "data": json.loads(content) if content else {}}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            return {"status": e.code, "error": err_json.get("detail", err_body)}
        except Exception:
            return {"status": e.code, "error": err_body}
    except Exception as e:
        return {"status": 500, "error": str(e)}


def handle_tool_call(name: str, args: dict) -> str:
    if name == "mem0_search_memory":
        query = args.get("query", "")
        project = args.get("project", "all")
        category = args.get("category", "all")
        limit = args.get("limit", 5)

        payload = {
            "query": query,
            "project": None if project == "all" else project,
            "category": None if category == "all" else category,
            "limit": limit
        }
        res = http_request("POST", "/api/v1/memories/search", data=payload)
        if "error" in res:
            return f"Mem0 Error: {res['error']}"
        
        results = res.get("data", [])
        if not results:
            return "No matching memories found in local vector database."
        
        output = [f"Found {len(results)} relevant memories:"]
        for idx, item in enumerate(results, 1):
            score = f" (relevance: {int(item.get('relevance_score', 0) * 100)}%)" if 'relevance_score' in item else ""
            output.append(
                f"\n[{idx}] [ID: {item.get('id')}]{score}\n"
                f"Project: {item.get('project', 'general')} | Category: {item.get('category', 'general')}\n"
                f"Tags: {', '.join(item.get('tags', []))}\n"
                f"Memory: {item.get('content')}"
            )
        return "\n".join(output)

    elif name == "mem0_add_memory":
        content = args.get("content", "")
        project = args.get("project", "general")
        category = args.get("category", "guideline")
        tags = args.get("tags", [])
        metadata = args.get("metadata", {})

        payload = {
            "content": content,
            "project": project,
            "category": category,
            "tags": tags,
            "metadata": metadata,
            "user_id": "default"
        }
        res = http_request("POST", "/api/v1/memories", data=payload)
        if "error" in res:
            return f"Mem0 Error: {res['error']}"
        
        created = res.get("data", {})
        return f"Successfully stored memory (ID: {created.get('id')}) for project '{project}' [{category}]."

    elif name == "mem0_list_memories":
        project = args.get("project", "all")
        category = args.get("category", "all")
        limit = args.get("limit", 15)

        params = {"limit": limit}
        if project != "all":
            params["project"] = project
        if category != "all":
            params["category"] = category

        res = http_request("GET", "/api/v1/memories", params=params)
        if "error" in res:
            return f"Mem0 Error: {res['error']}"

        data = res.get("data", {})
        memories = data.get("memories", [])
        total = data.get("total", 0)
        if not memories:
            return "No memories stored yet."

        output = [f"Total Memories: {total} (showing {len(memories)}):"]
        for idx, item in enumerate(memories, 1):
            output.append(
                f"\n[{idx}] [ID: {item.get('id')}]\n"
                f"Project: {item.get('project')} | Category: {item.get('category')} | Tags: {', '.join(item.get('tags', []))}\n"
                f"Content: {item.get('content')}"
            )
        return "\n".join(output)

    elif name == "mem0_get_memory":
        mem_id = args.get("memory_id", "")
        res = http_request("GET", f"/api/v1/memories/{mem_id}")
        if "error" in res:
            return f"Mem0 Error: {res['error']}"
        return json.dumps(res.get("data", {}), indent=2)

    elif name == "mem0_update_memory":
        mem_id = args.get("memory_id", "")
        payload = {}
        for k in ["content", "project", "category", "tags"]:
            if k in args and args[k] is not None:
                payload[k] = args[k]

        res = http_request("PUT", f"/api/v1/memories/{mem_id}", data=payload)
        if "error" in res:
            return f"Mem0 Error: {res['error']}"
        return f"Successfully updated memory '{mem_id}'."

    elif name == "mem0_delete_memory":
        mem_id = args.get("memory_id", "")
        res = http_request("DELETE", f"/api/v1/memories/{mem_id}")
        if "error" in res:
            return f"Mem0 Error: {res['error']}"
        return f"Successfully deleted memory '{mem_id}' from vector database."

    elif name == "mem0_get_stats":
        res = http_request("GET", "/api/v1/stats")
        if "error" in res:
            return f"Mem0 Error: {res['error']}"
        return json.dumps(res.get("data", {}), indent=2)

    return f"Unknown tool: {name}"


def send_response(response: dict):
    line = json.dumps(response)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "mem0",
                        "version": "1.0.0"
                    }
                }
            })
        elif method == "notifications/initialized":
            # No response needed for notification
            pass
        elif method == "tools/list":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": TOOLS
                }
            })
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                result_text = handle_tool_call(tool_name, tool_args)
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": str(result_text)
                            }
                        ]
                    }
                })
            except Exception as e:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                })
        elif method == "ping":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            })
        else:
            if req_id is not None:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                })


if __name__ == "__main__":
    main()
