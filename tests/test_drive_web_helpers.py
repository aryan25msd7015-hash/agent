from skills.drive_web_helpers import normalize_query, pick_first_visible


class _FakeLocator:
    def __init__(self, count: int, visible: bool = True) -> None:
        self._count = count
        self._visible = visible

    def count(self) -> int:
        return self._count

    @property
    def first(self) -> "_FakeLocator":
        return self

    def is_visible(self) -> bool:
        return self._visible


def test_normalize_query() -> None:
    assert normalize_query("  Quarterly   Report  ") == "quarterly report"


def test_pick_first_visible() -> None:
    locs = [_FakeLocator(0), _FakeLocator(2, True), _FakeLocator(1)]
    picked = pick_first_visible(locs)
    assert picked is not None
    assert picked.count() == 2
