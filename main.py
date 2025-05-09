from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from TikTokApi import TikTokApi
import threading
import time

app = Flask(__name__)
api = TikTokApi.get_instance()

# Substitua pelos usernames desejados
USER1 = 'lizx.macedo'
USER2 = 'euantonelabraga'

# Armazenamento dos dados históricos
history = {
    USER1: [],
    USER2: []
}

lock = threading.Lock()

def fetch_followers(username):
    try:
        user = api.get_user(username)
        return user.stats['followerCount']
    except Exception as e:
        print(f"Erro ao buscar dados de {username}: {e}")
        return None

def update_history():
    with lock:
        for user in [USER1, USER2]:
            count = fetch_followers(user)
            if count is not None:
                history[user].append((time.time(), count))
                # Mantém apenas os últimos 10 registros (10 minutos)
                if len(history[user]) > 10:
                    history[user].pop(0)

def calculate_projection():
    with lock:
        if len(history[USER1]) < 2 or len(history[USER2]) < 2:
            return None  # Dados insuficientes

        # Cálculo da taxa de ganho/perda por minuto
        def rate(data):
            times, counts = zip(*data)
            delta_time = times[-1] - times[0]
            delta_count = counts[-1] - counts[0]
            return delta_count / (delta_time / 60)  # seguidores por minuto

        rate1 = rate(history[USER1])
        rate2 = rate(history[USER2])
        current_diff = history[USER1][-1][1] - history[USER2][-1][1]
        rate_diff = rate2 - rate1

        if rate_diff <= 0:
            return None  # USER2 não está alcançando USER1

        minutes_to_zero = current_diff / rate_diff
        return minutes_to_zero

@app.route('/status', methods=['GET'])
def status():
    with lock:
        count1 = history[USER1][-1][1] if history[USER1] else None
        count2 = history[USER2][-1][1] if history[USER2] else None
        diff = count1 - count2 if count1 is not None and count2 is not None else None
        projection = calculate_projection()
        return jsonify({
            USER1: count1,
            USER2: count2,
            'difference': diff,
            'minutes_to_overtake': projection
        })

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_history, 'interval', minutes=1)
    scheduler.start()
    update_history()  # Inicializa com dados imediatos
    app.run(host='0.0.0.0', port=5000)