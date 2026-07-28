from skills.power import keep_awake_windows, wake_on_lan


def test_keep_awake_unsupported_or_ok() -> None:
    res = keep_awake_windows(True)
    assert res["status"] in {"enabled", "unsupported", "cleared"}


def test_wake_on_lan_handles_invalid_mac() -> None:
    res = wake_on_lan("not-a-mac")
    assert res["status"] in {"sent", "failed"}
