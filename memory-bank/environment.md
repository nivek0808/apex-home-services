# Environment - Apex Home Services

## Operating Environment Details

### System Information
- **OS:** Linux (Debian/Ubuntu-based, based on apt package manager)
- **Container:** Proxmox LXC container (detected from .bash_history)
- **IDE:** code-server (VS Code in browser)
- **Working Directory:** /root/aiClientSupport

### Available Tools (from detection)
- **Package Managers:** apt, pip, npm
- **Languages/Runtimes:** python3, node, bash
- **CLI Tools:** git, curl, make, grep, sed, awk, sudo
- **Other:** Docker (to be installed/verified)

### Software Installed
- **Python3:** Available (installed via apt)
- **pip/pip3:** Available (installed via apt)
- **Git:** Available
- **Node.js/npm:** Available
- **Docker/Docker Compose:** To be verified/installed

### Network & Services
- **code-server:** Running locally (accessed via browser)
- **Local LLM (Qwen):** Expected at http://localhost:8080/v1 (not yet confirmed running)
- **Invoice Ninja Mirror:** Planned for port 8003
- **n8n Mirror:** Planned for port 5678
- **Cal.com Mirror:** Planned for port 3000

### Container Details
- **Platform:** Proxmox VE LXC container
- **Container ID Reference:** 900 (from .bash_history lxc-attach command)
- **Services Managed:** systemd (systemctl available)

---
*Last updated: 2026-07-30 - Initial environment discovery*