import os

def redis_config(db_url, db_port, db_database, db_pass, db_user):
    return {
        "CACHE_TYPE": "RedisCache",
        # this is fine since cache is only invalid after pipeline run
        "CACHE_DEFAULT_TIMEOUT": 60 * 60 * 23,
        "CACHE_REDIS_HOST": db_url,
        "CACHE_REDIS_PORT": db_port or 6379,
        "CACHE_REDIS_DB": db_database or 1,
        "CACHE_REDIS_PASSWORD": db_pass or "",
        "CACHE_REDIS_USER": db_user or "",
        # if the source code changes, the cache is invalidated
        "CACHE_SOURCE_CHECK": True,
        "DEBUG": True if os.environ.get("DEBUG_REDIS") == "true" else False,
    }
