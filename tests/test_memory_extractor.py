from app.memory.extractor import detect_memory_action


def test_detect_memory_save_action() -> None:
    action = detect_memory_action("remember that my favorite language is python")
    assert action.action == "save"
    assert action.key == "my favorite language"
    assert action.value == "python"


def test_detect_memory_recall_action() -> None:
    action = detect_memory_action("recall my favorite language")
    assert action.action == "recall"
    assert action.key == "my favorite language"


def test_detect_memory_none_action() -> None:
    action = detect_memory_action("tell me a joke")
    assert action.action == "none"
