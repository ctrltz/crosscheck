import os

from redis import Redis


redis_app = Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'),
                           decode_responses=True)


# Redis keys in use
class RedisRequests:
    HASH = 'requests'
    KEY_TOTAL = 'total'
    KEY_COMPLETED = 'completed'
    KEY_FAILED_EMPTY = 'failed_empty'
    KEY_FAILED_OTHER = 'failed_other'


class RedisPapers:
    HASH = 'papers'
    KEY_PROCESSED = 'processed'
    KEY_NOT_FOUND = 'not_found'
