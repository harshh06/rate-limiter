from models import TokenBucket
from math import floor
from datetime import datetime


def update_tokens(client_bucket: TokenBucket, current_time: datetime.now) -> int:
    last_refill_time = client_bucket.last_refill_time
    elapsed_time = current_time - last_refill_time
    elapsed_time_in_sec = elapsed_time.total_seconds()
    new_tokens_added = elapsed_time_in_sec * client_bucket.refill_rate
    new_total_tokens = floor((new_tokens_added) + client_bucket.tokens)
    updated_tokens = min( new_total_tokens, client_bucket.capacity )
    client_bucket.last_refill_time = current_time
    return updated_tokens
