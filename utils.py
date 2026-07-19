from models import TokenBucket
from math import floor
from datetime import datetime


def update_tokens(client: dict, current_time: float) -> int:
    last_refill_time = float(client['last_refill_time'])
    
    # current_time and last_refill_time are both already in seconds (floats), 
    # so we can just subtract them directly! No need for .total_seconds()
    elapsed_time_in_sec = current_time - last_refill_time
    
    # We fetch capacity based on the tier (since we don't store it in Redis)
    tier = client.get('tier', 'free')
    
    # In models.py, free=3, premium=10
    capacity = 10 if tier == 'premium' else 3
    refill_rate = 10
    
    new_tokens_added = elapsed_time_in_sec * refill_rate
    # strings to float
    new_total_tokens = floor(new_tokens_added + float(client['tokens']))
    updated_tokens = min(new_total_tokens, capacity)
    
    return updated_tokens
