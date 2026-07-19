local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local current_time = tonumber(ARGV[3])

-- current/ default values

local tokens = capacity
local last_refill_time = current_time

-- hash -> client if present
local hash = redis.call('HGETALL', key)

-- if client exist, update values through for loop
if #hash > 0 then
    for i = 1, #hash, 2 do
        if hash[i] == 'tokens' then
            tokens = tonumber(hash[i+1])
        elseif hash[i] == 'last_refill_time' then
            last_refill_time = tonumber(hash[i+1])
        end
    end
end


-- refill tokens based on elapsed time 
local elapsed_time = current_time - last_refill_time
if elapsed_time < 0 then
    elapsed_time = 0
end

local new_tokens = math.floor(tokens + (elapsed_time * refill_rate))
if new_tokens > capacity then
    new_tokens = capacity
end

--  check if they have enough tokens
local allowed = 0
if new_tokens >= 1 then
    new_tokens = new_tokens - 1
    allowed = 1
end

-- save new state back to redis
redis.call('HSET', key, 'tokens', new_tokens, 'last_refill_time', current_time)


return {allowed, tostring(new_tokens)}



