from collections import defaultdict
from datetime import datetime, timedelta
import threading

MAX_MESSAGES   = 20
WINDOW_SECONDS = 60

_message_log = defaultdict(list)
_lock = threading.Lock()


def is_rate_limited(user_id: str) -> bool:
    now    = datetime.utcnow()
    cutoff = now - timedelta(seconds=WINDOW_SECONDS)
    with _lock:
        _message_log[user_id] = [t for t in _message_log[user_id] if t > cutoff]
        if len(_message_log[user_id]) >= MAX_MESSAGES:
            return True
        _message_log[user_id].append(now)
        return False


def get_message_count(user_id: str) -> int:
    now    = datetime.utcnow()
    cutoff = now - timedelta(seconds=WINDOW_SECONDS)
    with _lock:
        return len([t for t in _message_log[user_id] if t > cutoff])
