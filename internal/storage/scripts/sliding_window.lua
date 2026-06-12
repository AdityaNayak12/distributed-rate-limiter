local redis_key = KEYS[1]
local now = tonumber(ARGV[1])
local window_size = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]

local window_start = now - window_size

-- Remove old entries older than window_start
redis.call('ZREMRANGEBYSCORE', redis_key, 0, window_start)

-- Count requests in window
local count = redis.call('ZCARD', redis_key)

local allowed = 0
local remaining = limit - count

if count < limit then
    -- Allow request, add unique member
    redis.call('ZADD', redis_key, now, member)
    allowed = 1
    remaining = remaining - 1
end

-- Set expiry to window size + 1 to auto-cleanup
redis.call('EXPIRE', redis_key, math.ceil(window_size) + 1)

return {allowed, remaining}
