from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import timedelta, datetime
from fastapi import status, HTTPException, FastAPI


from utils import update_tokens

from models import TokenBucket


app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello from rate-limiter!"}


@app.get("/api/ping")
def ping(request: Request):
    client_id = request.headers.get('X-Client-Id')
    if not client_id:
        raise HTTPException(status_code=400, detail="X-Client-Id header required")

    client_tier=request.query_params["tier"]

    if client_id not in bucket:
        bucket[client_id] = TokenBucket(tier=client_tier)

    current_time = datetime.now()
    bucket[client_id].tokens = update_tokens(bucket[client_id], current_time)

    if bucket[client_id].tokens >= 1:
        bucket[client_id].tokens -= 1
        return JSONResponse(
            content={"message": "Server pinged"},
            status_code=200,
            headers={
                "X-RateLimit-Limit": str(bucket[client_id].capacity),
                "X-RateLimit-Remaining": str(bucket[client_id].tokens)
            }
        )
    else :
        seconds_until_next_token = (1 - bucket[client_id].tokens) / bucket[client_id].refill_rate
        reset_time = current_time + timedelta(seconds=seconds_until_next_token)
        raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit reached",
                headers={
                    "X-RateLimit-Limit": str(bucket[client_id].capacity),
                    "X-RateLimit-Remaining": str(bucket[client_id].tokens),
                    "X-RateLimit-Reset": str(reset_time)
                }
            )


bucket = {}

def main():
    print("Hello from rate-limiter!")


if __name__ == "__main__":
    main()
