from fastapi import FastAPI
from TikTokApi import TikTokApi
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import time

app = FastAPI()
scheduler = AsyncIOScheduler()

# Iniciar o navegador via Playwright
api = TikTokApi.get_instance(use_test_endpoints=True)
asyncio.get_event_loop().run_until_complete(api.create_sessions())

# Usuários fixos
USER1 = "lizx.macedo"
USER2 = "euantonelabraga"
key = f"{USER1}_{USER2}"
trackers = {
    key: {'history': [], 'followers': {'user1': 0, 'user2': 0}}
}

async def poll_counts():
    try:
        u1 = api.get_user(USER1)
        u2 = api.get_user(USER2)
        c1 = u1.stats['followerCount']
        c2 = u2.stats['followerCount']
        diff = c1 - c2
        data = trackers[key]
        data['followers'] = {'user1': c1, 'user2': c2}
        data['history'].append((time.time(), diff))
        if len(data['history']) > 10:
            data['history'].pop(0)
        print(f"Updated counts: {USER1}: {c1}, {USER2}: {c2}, Diff: {diff}")
    except Exception as e:
        print(f"Error polling: {e}")

@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(poll_counts, 'interval', minutes=1, id=key)
    asyncio.get_event_loop().create_task(poll_counts())
    scheduler.start()

@app.get("/compare")
def compare():
    data = trackers[key]
    c1 = data['followers']['user1']
    c2 = data['followers']['user2']
    diff = c1 - c2
    rates = []
    hist = data['history']
    for i in range(len(hist) - 1):
        prev = hist[i][1]
        curr = hist[i + 1][1]
        rates.append(prev - curr)
    avg_rate = sum(rates) / len(rates) if rates else None
    est_minutes = abs(diff) / avg_rate if avg_rate and avg_rate > 0 else None
    return {
        'user1': {'username': USER1, 'followers': c1},
        'user2': {'username': USER2, 'followers': c2},
        'difference': diff,
        'average_rate_per_minute': avg_rate,
        'estimated_minutes_to_crossover': est_minutes
    }