
from datetime import datetime

TIER_CAPACITY = {"free": 3, "premium": 10}

class TokenBucket():
    def __init__(self, tier: str, refill_rate=10):
        self.tier = tier
        self.capacity = TIER_CAPACITY.get(tier, 10)
        self.tokens = self.capacity
        self.refill_rate = refill_rate #tokens added per second
        self.last_refill_time = datetime.now()
