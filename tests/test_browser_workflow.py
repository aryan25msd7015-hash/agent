from brain.orchestrator import Orchestrator


def test_browse_workflow_route_parsing() -> None:
    orch = Orchestrator()
    res = orch.run("browse https://example.com workflow: click=#hero,fill=#q:hello")
    assert res["action"] == "browser_workflow"
    assert "status" in res
