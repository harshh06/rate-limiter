from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import timedelta, datetime
from fastapi import FastAPI

from utils import update_tokens

from models import TokenBucket


app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello from rate-limiter!"}


@app.middleware("http")
async def check_rate_limit(request: Request, call_next):

    if request.url.path in ["/", "/docs", "/openapi.json"]:
        return await call_next(request)

    client_id = request.headers.get('X-Client-Id')
    if not client_id:
        return JSONResponse(
                content={"detail": "X-Client-Id header required"},
                status_code=400
            )

    client_tier=request.query_params["tier"]

    if client_id not in bucket:
        bucket[client_id] = TokenBucket(tier=client_tier)

    current_time = datetime.now()
    bucket[client_id].tokens = update_tokens(bucket[client_id], current_time)

    if bucket[client_id].tokens >= 1:
        bucket[client_id].tokens -= 1
        response = await call_next(request)
        response.headers = {
                    "X-RateLimit-Limit": str(bucket[client_id].capacity),
                    "X-RateLimit-Remaining": str(bucket[client_id].tokens)
                }
        return response
        
    else :
        seconds_until_next_token = (1 - bucket[client_id].tokens) / bucket[client_id].refill_rate
        reset_time = current_time + timedelta(seconds=seconds_until_next_token)
        return JSONResponse(
                content={"detail": "Rate limit reached"},
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(bucket[client_id].capacity),
                    "X-RateLimit-Remaining": str(bucket[client_id].tokens),
                    "X-RateLimit-Reset": str(reset_time)
                }
            )

@app.get("/api/ping")
def ping(request: Request):
    client_id = request.headers.get('X-Client-Id')
    return JSONResponse(
                content={"message": "Server pinged"},
                status_code=200
            )

@app.get("/api/tweets")
def tweets(request: Request):
    client_id = request.headers.get('X-Client-Id')
    return JSONResponse(
                content={"message": "Tweet!"},
                status_code=200
            )

bucket = {}

def main():
    print("Hello from rate-limiter!")


if __name__ == "__main__":
    main()
