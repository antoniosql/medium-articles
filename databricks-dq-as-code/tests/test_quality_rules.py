from src.common.quality_rules import load_rules_as_dict


class _FakeRow(dict):
    def __getattr__(self, item):
        return self[item]


class _FakeFilteredFrame:
    def select(self, *_args, **_kwargs):
        return self

    def collect(self):
        return [
            {"rule_name": "rule_a", "constraint_sql": "id IS NOT NULL"},
            {"rule_name": "rule_b", "constraint_sql": "amount >= 0"},
        ]


class _FakeRead:
    def table(self, _name):
        return self

    def filter(self, _expr):
        return _FakeFilteredFrame()


class _FakeSpark:
    read = _FakeRead()



def test_load_rules_as_dict_returns_expected_shape():
    rules = load_rules_as_dict(_FakeSpark(), "x.y.z", "tag1", "warn")
    assert rules == {
        "rule_a": "id IS NOT NULL",
        "rule_b": "amount >= 0",
    }
