from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import timedelta, datetime
from fastapi import FastAPI
from redis.asyncio import Redis

r = Redis(host='localhost', port=6379, decode_responses=True)

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

    client_tier = request.query_params.get("tier", "free")
    
    current_time = datetime.now().timestamp()
    capacity = 100 if client_tier == 'premium' else 10
    refill_rate = 20 if client_tier == 'premium' else 2

    with open("rate_limiter.lua", "r") as file:
        lua_script_string = file.read()

    result = await r.eval(
        lua_script_string,
        1,
        client_id,
        capacity,
        refill_rate,
        current_time
    )

    allowed = result[0] == 1
    updated_tokens = float(result[1])

    if allowed:
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(capacity)
        response.headers["X-RateLimit-Remaining"] = str(updated_tokens)
        return response
        
    else:
        # Prevent division by zero or negative seconds if tokens dipped for some reason
        seconds_until_next_token = max(0, (1 - updated_tokens) / refill_rate)
        reset_time = datetime.fromtimestamp(current_time) + timedelta(seconds=seconds_until_next_token)
        return JSONResponse(
                content={"detail": "Rate limit reached"},
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(capacity),
                    "X-RateLimit-Remaining": str(updated_tokens),
                    "X-RateLimit-Reset": str(reset_time)
                }
            )

@app.get("/api/ping")
def ping():
    return JSONResponse(
                content={"message": "Server pinged"},
                status_code=200
            )

@app.get("/api/tweets")
def tweets():
    return JSONResponse(
                content={"message": "Tweet!"},
                status_code=200
            )

def main():
    print("Hello from rate-limiter!")


if __name__ == "__main__":
    main()
