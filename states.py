from typing import Any, Optional

_state: dict[int, dict[str, Any]] = {}

def set_state(user_id: int, step: str, **kwargs: Any) -> None:
    _state[user_id] = {"step": step, **kwargs}

def get_state(user_id: int) -> Optional[dict[str, Any]]:
    return _state.get(user_id)

def clear_state(user_id: int) -> None:
    _state.pop(user_id, None)

def in_state(user_id: int, step: str) -> bool:
    s = _state.get(user_id)
    return s is not None and s.get("step") == step
