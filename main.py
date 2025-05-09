from flask import Flask, jsonify
from TikTokApi import TikTokApi
from apscheduler.schedulers.background import BackgroundScheduler
import time
import threading

app = Flask(__name__)

# Dados iniciais
usernames = ["lizx.macedo", "euantonelabraga"]
followers_history = {
    "lizx.macedo": [],
    "euantonelabraga": []
}
lock = threading.Lock()

def fetch_followers():
    with TikTokApi() as api:
        for username in usernames:
            try:
                user_info = api.user(username=username).info()
                followers_count = user_info['stats']['followerCount']
                timestamp = time.time()
                with lock:
                    followers_history[username].append((timestamp, followers_count))
                    # Mantém apenas os últimos 10 registros (10 minutos)
                    if len(followers_history[username]) > 10:
                        followers_history[username].pop(0)
            except Exception as e:
                print(f"Erro ao buscar dados de {username}: {e}")

# Agenda a função para rodar a cada minuto
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_followers, 'interval', minutes=1)
scheduler.start()

@app.route('/followers', methods=['GET'])
def get_followers_data():
    with lock:
        data = {}
        for username in usernames:
            if followers_history[username]:
                data[username] = followers_history[username][-1][1]
            else:
                data[username] = None

        if None in data.values():
            return jsonify({"error": "Dados insuficientes para calcular."}), 500

        diff = data[usernames[0]] - data[usernames[1]]

        # Calcula a média de ganho/perda por minuto nos últimos 10 minutos
        rates = {}
        for username in usernames:
            history = followers_history[username]
            if len(history) >= 2:
                deltas = [
                    (history[i][1] - history[i - 1][1]) / ((history[i][0] - history[i - 1][0]) / 60)
                    for i in range(1, len(history))
                ]
                rates[username] = sum(deltas) / len(deltas)
            else:
                rates[username] = 0

        # Estima o tempo para o usuário 2 alcançar o usuário 1
        rate_diff = rates[usernames[1]] - rates[usernames[0]]
        if rate_diff <= 0:
            eta = None  # Nunca alcançará
        else:
            eta = diff / rate_diff  # em minutos

        return jsonify({
            "followers": data,
            "difference": diff,
            "rates_per_minute": rates,
            "estimated_minutes_to_overtake": eta
        })

if __name__ == '__main__':
    app.run(debug=True)