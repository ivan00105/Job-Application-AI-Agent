# Security Recommendations for Code Execution

## Current Status: ⚠️ DEVELOPMENT ONLY

The code execution feature is **NOT safe for production** in its current form.

## Quick Fixes (Implement Now)

### 1. Enable Secure Code Executor

Replace the basic executor with the secure version:

```python
# In coding_handler.py
from services.games.secure_code_executor import SecureCodeExecutor

self.code_executor = SecureCodeExecutor(timeout_seconds=10, max_memory_mb=128)
```

### 2. Run Backend as Unprivileged User

```bash
# Create dedicated user
sudo useradd -r -s /bin/false codeexecutor

# Run backend as this user
sudo -u codeexecutor python main.py
```

### 3. Set OS-Level Resource Limits

Add to your system configuration:

```bash
# /etc/security/limits.conf
codeexecutor soft nproc 10
codeexecutor soft nofile 100
codeexecutor hard as 128000  # 128MB memory
```

### 4. Disable Network Access

Use firewall rules or network namespaces to prevent code from making network requests.

## Production Solution: Docker

See `docs/CODE_EXECUTION_SECURITY.md` for Docker implementation guide.

## Alternative: Use External Service

Consider using:
- **Judge0 API** (open source, self-hosted)
- **Piston** (fast, self-hosted)
- **CodeX Execution API** (cloud-based)

These services are designed for secure code execution.

