# mem0-mcp-server

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![MCP](https://img.shields.io/badge/Model%20Context%20Protocol-Compatible-purple.svg)](https://modelcontextprotocol.io/)
[![Python](https://img.shields.io/badge/Python-3.12-yellow.svg)](https://www.python.org/)

A self-hosted, 100% local, zero-external-API **Mem0 Memory Server** and **Web Management Dashboard** integrated as a Model Context Protocol (MCP) tool provider for any MCP-compatible AI client (Claude, Cursor, Windsurf, Antigravity, etc.).

This system gives AI coding assistants long-term memory across conversations—persisting project architecture decisions, user preferences, coding guidelines, and technical facts.

---

## 🌟 Key Features

- 🧠 **100% Local & Offline**: Embedded local vector database (Qdrant) + CPU embeddings (`BAAI/bge-small-en-v1.5` via FastEmbed). No OpenAI, Gemini, or external API keys needed!
- 🐳 **Dockerized & Isolated**: Runs in a lightweight container on custom port **`28842`** (eliminates local port collisions).
- 🌐 **Modern Web Dashboard**: Clean Dark/Light UI at `http://localhost:28842` for searching, editing, adding, and inspecting memories and revision histories.
- 🤖 **Turnkey MCP Server**: Standard-library MCP stdio server with zero host dependencies.
- 📂 **Multi-Project & Categorized**: Organize memories by Project (`fieldnation`, `personal`, `general`), Category (`architecture`, `preference`, `guideline`, `decision`, `fact`), and custom Tags.
- 💾 **Persistent & Private**: Vectors and SQLite metadata are stored in `./data/` and excluded from Git.

---

## 🚀 Quick Start

### 1. Clone & Start Container

```bash
git clone https://github.com/mkshuvo/mem0-local-server.git
cd mem0-local-server

# Build & launch container
docker compose up -d --build
```

Access the Web Management Dashboard at [**http://localhost:28842**](http://localhost:28842).

### 2. Configure MCP Client

Add `mem0-mcp-server` to your MCP configuration file:

#### Antigravity (`~/.gemini/config/mcp_config.json`)
```json
{
  "mcpServers": {
    "mem0": {
      "command": "/opt/homebrew/bin/python3",
      "args": [
        "/path/to/mem0-local-server/mcp/mem0_mcp.py"
      ],
      "env": {
        "MEM0_SERVER_URL": "http://localhost:28842"
      }
    }
  }
}
```

#### Claude Desktop (`claude_desktop_config.json`) / Cursor / Windsurf
```json
{
  "mcpServers": {
    "mem0": {
      "command": "python3",
      "args": [
        "/absolute/path/to/mem0-local-server/mcp/mem0_mcp.py"
      ],
      "env": {
        "MEM0_SERVER_URL": "http://localhost:28842"
      }
    }
  }
}
```

---

## 🛠️ MCP Tools Reference

| Tool | Description |
| :--- | :--- |
| `mem0_search_memory` | Semantic vector search across all memories by query, project, or category. |
| `mem0_add_memory` | Store a new insight, preference, guideline, or fact across conversations. |
| `mem0_list_memories` | List recent memories with optional project or category filters. |
| `mem0_get_memory` | Retrieve a specific memory with full metadata and revision history. |
| `mem0_update_memory` | Update or refine existing memory content, tags, or category. |
| `mem0_delete_memory` | Remove an obsolete memory from vector storage. |
| `mem0_get_stats` | Inspect memory count, vector DB health, and system metrics. |

---

## 📁 Repository Structure

```
mem0-local-server/
├── Dockerfile                  # Container definition (FastEmbed + Qdrant)
├── docker-compose.yml          # Compose file (Port 28842 + persistent ./data)
├── requirements.txt            # Python backend dependencies
├── server/
│   ├── main.py                 # FastAPI application & static server
│   ├── mem0_service.py         # Qdrant vector engine + FastEmbed + SQLite
│   └── routes.py               # REST API endpoints
├── static/
│   ├── index.html              # Web Manager Dashboard
│   ├── style.css               # Dark theme UI
│   └── app.js                  # Frontend client logic
├── mcp/
│   └── mem0_mcp.py             # Pure Python stdio MCP server (0 host dependencies)
├── scripts/
│   ├── start.sh                # Start container
│   ├── stop.sh                 # Stop container
│   ├── status.sh               # Healthcheck & metrics script
│   └── backup.sh               # JSON backup utility
├── data/                       # Local vector DB & SQLite (gitignored)
└── LICENSE                     # MIT License
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.
