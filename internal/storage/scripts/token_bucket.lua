local redis_key = KEYS[1]
local now = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local capacity = tonumber(ARGV[3])
local ttl = tonumber(ARGV[4])

-- Get current tokens and last_refill from Redis
local tokens = redis.call('HGET', redis_key, 'tokens')
local last_refill = redis.call('HGET', redis_key, 'last_refill')

if not tokens or not last_refill then
    tokens = capacity
    last_refill = now
else
    tokens = tonumber(tokens)
    last_refill = tonumber(last_refill)
end

-- Refill tokens
local elapsed = now - last_refill
local refill = elapsed * refill_rate
tokens = math.min(capacity, tokens + refill)
last_refill = now

-- Check if allowed
local allowed = 0
if tokens >= 1 then
    tokens = tokens - 1
    allowed = 1
end

-- Save updated state
redis.call('HSET', redis_key, 'tokens', tokens, 'last_refill', last_refill)
redis.call('EXPIRE', redis_key, ttl)

return {allowed, math.floor(tokens)}
