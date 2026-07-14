from fastapi.responses import JSONResponse
from fastapi import Response
from datetime import timedelta
from math import floor
from fastapi import status
from fastapi import HTTPException
from fastapi import FastAPI
from datetime import time, datetime

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello from rate-limiter!"}


@app.get("/api/ping")
def ping():
    current_time = datetime.now()
    last_refill_time = bucket["alice"].last_refill_time
    elapsed_time = current_time - last_refill_time
    elapsed_time_in_sec = elapsed_time.total_seconds()
    updated_tokens = min( floor((elapsed_time_in_sec * bucket["alice"].refill_rate) + bucket["alice"].tokens), bucket["alice"].capacity )
    bucket["alice"].last_refill_time=current_time
    bucket["alice"].tokens = updated_tokens

    print("elapsed time", elapsed_time_in_sec)
    print("tokens left", bucket["alice"].tokens)

    if bucket["alice"].tokens >= 1:
        bucket["alice"].tokens -= 1
        return JSONResponse(
            content={"message": "Server pinged"},
            status_code=200,
            headers={
                "X-RateLimit-Limit": str(bucket["alice"].capacity),
                "X-RateLimit-Remaining": str(bucket["alice"].tokens)
            }
        )
    else :
        seconds_until_next_token = (1 - bucket["alice"].tokens) / bucket["alice"].refill_rate
        reset_time = current_time + timedelta(seconds=seconds_until_next_token)
        raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit reached",
                headers={
                    "X-RateLimit-Limit": str(bucket["alice"].capacity),
                    "X-RateLimit-Remaining": str(bucket["alice"].tokens),
                    "X-RateLimit-Reset": str(reset_time)
                }
            )


class TokenBucket():
    def __init__(self, tokens=10, capacity=10, refill_rate=10):
        self.tokens = tokens
        self.capacity = capacity
        self.refill_rate = refill_rate #tokens added per second
        self.last_refill_time = datetime.now()
        

bucket = {
    "alice": TokenBucket()
}

def main():
    print("Hello from rate-limiter!")


if __name__ == "__main__":
    main()
