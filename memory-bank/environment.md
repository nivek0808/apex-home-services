# Environment - Apex Home Services

## Operating Environment Details

### System Information
- **OS:** Linux (Debian/Ubuntu-based, based on apt package manager)
- **Container:** Proxmox LXC container (detected from .bash_history)
- **IDE:** code-server (VS Code in browser)
- **Working Directory:** /root/workspace/aiClientSupport

### Runtime Environment
- **Python:** 3.12 (verified in .venv)
- **Virtual Environment:** `.venv` with all project dependencies installed
- **Package Manager:** pip (Python), apt (system), npm (Node.js)
- **Database:** SQLite via SQLAlchemy (`apex_sandbox.db`, 45KB)
- **Web Server:** Uvicorn (ASGI) via FastAPI
- **HTTP Client:** httpx (async)

### Software Installed
- **Python3:** 3.12 (in .venv)
- **pip/pip3:** Available
- **Git:** Available
- **Node.js/npm:** Available
- **Docker/Docker Compose:** To be verified/installed
- **Project Dependencies:** fastapi==0.115.6, uvicorn==0.34.0, sqlalchemy==2.0.36, pydantic==2.10.4, httpx==0.28.1, jinja2==3.1.5, python-multipart==0.0.20, python-dotenv==1.0.1

### Network & Services
- **FastAPI Backend:** http://localhost:8000 (port configurable)
- **code-server:** Running locally (accessed via browser)
- **Local LLM (Qwen):** Expected at http://localhost:8080/v1 (not yet confirmed running)
- **Invoice Ninja Mirror:** Planned for port 8003
- **n8n Mirror:** Planned for port 5678
- **Cal.com Mirror:** Planned for port 3000

### Container Details
- **Platform:** Proxmox VE LXC container
- **Container ID Reference:** 900 (from .bash_history lxc-attach command)
- **Services Managed:** systemd (systemctl available)

## UI & Design System Specs

### Component Libraries & Role Division
1. **shadcn/ui (Base Primitives & Core Application UI)**
   - **Scope**: Buttons, inputs, forms, dialogs, dropdowns, navigation menus, tabs, cards, tables, and admin dashboards.
   - **Usage Rule**: Always check if a component exists in `shadcn/ui` first. Install via `npx shadcn@latest add <component>`.
2. **Magic UI (Refined Micro-Interactions)**
   - **Scope**: Subtle animated text, border beam effects, particle/grid backgrounds, marquee logos, interactive CTA buttons, and subtle hover states.
   - **Usage Rule**: Use for micro-interactions and interactive visual enhancements. Install via `npx shadcn@latest add https://magicui.design/r/<component>`.
3. **Aceternity UI (High-Impact Hero & Marketing Sections)**
   - **Scope**: Landing page hero sections, 3D tilt cards, background spotlight/grid beams, sticky scroll reveals, and feature showcases.
   - **Usage Rule**: Limit to 1–2 key sections per page (e.g., main Hero section or key client demo showcase). Install via `npx shadcn@latest add https://ui.aceternity.com/registry/<component>.json`.

### MCP Tool Usage
- **shadcn MCP**: Use available `shadcn` MCP tools to query component documentation and schemas before writing code.
- **21st.dev Magic UI MCP**: Use 21st.dev MCP tools (when active) to generate and insert pre-styled React/Tailwind blocks.

### Design Principles & Styling Constraints
- **Styling**: Tailwind CSS only. Do NOT write raw CSS files or inline `style={...}` attributes.
- **Color & Theme**: Dark/neutral background (`bg-background`), semantic color tokens (`text-muted-foreground`, `border-border`), and a single restrained primary accent color.
- **Layout & Spacing**: Generous section padding (`py-16 md:py-24`, `px-4 sm:px-6 lg:px-8`) and constrained max widths (`max-w-6xl` or `max-w-7xl mx-auto`).
- **Typography**: Clean hierarchy using `font-bold tracking-tight` for headings.
---
*Last updated: 2026-07-30 - Python 3.12, SQLite runtime, dependencies verified. Dashboard rebuilt with modern UI.*
