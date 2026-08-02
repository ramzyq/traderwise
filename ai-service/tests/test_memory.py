from services.memory import Message, MemoryStore


def test_save_get():
    m = MemoryStore()
    m.save("u1", [Message(role="user", content="hi")])
    hist = m.get("u1")
    assert len(hist) == 1
    assert hist[0].content == "hi"


def test_clear():
    m = MemoryStore()
    m.save("u1", [Message(role="user", content="hi")])
    m.clear("u1")
    assert m.get("u1") == []


def test_cap_at_20():
    m = MemoryStore()
    m.save("u1", [Message(role="user", content=f"m{i}") for i in range(25)])
    hist = m.get("u1")
    assert len(hist) == 20
    assert hist[0].content == "m5"