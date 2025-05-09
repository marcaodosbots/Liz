from fastapi import FastAPI
from TikTokApi import TikTokApi
import time
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

app = FastAPI()
api = TikTokApi()
scheduler = AsyncIOScheduler()

# Usuários fixos
USER1 = "lizx.macedo"
USER2 = "euantonelabraga"
key = f"{USER1}_{USER2}"
trackers = {
    key: {'history': [], 'followers': {'user1': 0, 'user2': 0}}
}

async def poll_counts():
    try:
        user1 = api.user(username=USER1)
        user2 = api.user(username=USER2)
        info1 = user1.info_full()
        info2 = user2.info_full()
        c1 = info1["userInfo"]["stats"]["followerCount"]
        c2 = info2["userInfo"]["stats"]["followerCount"]
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