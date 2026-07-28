# Run connector as Windows background service

## Option A: Task Scheduler (built-in)

1. Open Task Scheduler.
2. Create Task:
   - Name: `PersonalAgentConnector`
   - Run whether user is logged on or not.
3. Trigger: At startup.
4. Action:
   - Program/script: `python`
   - Arguments: `connector/runtime/agent.py`
   - Start in: your repository path (e.g. `D:\agent`)

## Option B: NSSM

1. Install NSSM.
2. Run:
   - `nssm install PersonalAgentConnector`
3. Configure:
   - Path: `python.exe`
   - Startup directory: repo directory
   - Arguments: `connector/runtime/agent.py`
4. Start service:
   - `nssm start PersonalAgentConnector`

The connector pings the gateway health endpoint and should be left running continuously.
