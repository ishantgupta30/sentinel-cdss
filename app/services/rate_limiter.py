import time
import asyncio

last_request_time = 0
COOLDOWN_SECONDS = 180  # 3 min between requests

async def check_rate_limit():
    global last_request_time
    now = time.time()
    elapsed = now - last_request_time
    if elapsed < COOLDOWN_SECONDS:
        wait = int(COOLDOWN_SECONDS - elapsed)
        raise Exception(f"Please wait {wait} seconds before next request.")
    last_request_time = now
