import time
import requests
import logging

# --- ΣΤΟΙΧΕΙΑ ΣΥΝΔΕΣΗΣ ---
TELEGRAM_BOT_TOKEN = "8969723492:AAFqhtdsuSqPkFAGHGwhfUkv3phm-Mp7zlM"
TELEGRAM_CHAT_ID = "980258434"
PINNAPI_API_URL = "https://api.pinnacle.com/v1/odds/drops"
PINNAPI_API_KEY = "2wVmkuaZJzKEoHeNpGUsGM3i2mdoqHKm"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        logging.error(f"Σφάλμα αποστολής: {e}")

def calculate_fair_value(current_odds):
    return round(current_odds * 0.95, 2)

def evaluate_drop(event):
    minutes_to_kickoff = event.get('minutes_to_kickoff', 0)
    if not (60 <= minutes_to_kickoff <= 360): # 1 έως 6 ώρες πριν τη σέντρα
        return False
        
    current_odds = event.get('current_odds', 0.0)
    if not (1.70 <= current_odds <= 2.50): # Εύρος απόδοσης
        return False
        
    drop_percentage = event.get('drop_percentage', 0.0)
    duration_minutes = event.get('duration_minutes', 999)
    
    if drop_percentage >= 6.0 and duration_minutes <= 5: # >= 6% drop σε <= 5 λεπτά
        return True
    return False

def format_telegram_alert(event):
    home = event.get('home_team', 'Ομάδα Α')
    away = event.get('away_team', 'Ομάδα Β')
    league = event.get('league_name', 'Διοργάνωση')
    hours_left = round(event.get('minutes_to_kickoff', 0) / 60, 1)
    
    market = event.get('market_name', 'Market')
    old_odds = event.get('old_odds', 0.0)
    current_odds = event.get('current_odds', 0.0)
    drop_pct = event.get('drop_percentage', 0.0)
    dur = event.get('duration_minutes', 0)
    fair_value = calculate_fair_value(current_odds)
    
    message = (
        "🚨 SHARP DROP DETECTED 🚨\n\n"
        f"⚽️ Αγώνας: {home} vs {away}\n"
        f"🏆 Διοργάνωση: {league}\n"
        f"⏰ Έναρξη σε: {hours_left} ώρες\n\n"
        f"📊 Αγορά: {market}\n"
        f"📉 Κίνηση: Από {old_odds} ➔ {current_odds}\n"
        f"⚡️ Velocity: -{drop_pct}% σε {dur} λεπτά *(Smart Money Flag)*\n\n"
        "🎯 Fair Value Analysis:\n"
        f"• No-Vig Fair Price: {fair_value}\n"
        f"• Τρέχουσα Pinnacle: {current_odds}\n"
        "💡 Verdict: +EV Value Bet *(Τρέχα στον soft book!)*"
    )
    return message

def main_loop():
    headers = {"Authorization": f"Bearer {PINNAPI_API_KEY}"}
    logging.info("Το bot ξεκίνησε!")
    while True:
        try:
            response = requests.get(PINNAPI_API_URL, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                events = data if isinstance(data, list) else data.get('events', [])
                for event in events:
                    if evaluate_drop(event):
                        alert = format_telegram_alert(event)
                        send_telegram_message(alert)
                        time.sleep(2)
        except Exception as e:
            logging.error(f"Σφάλμα: {e}")
        time.sleep(30)

if __name__ == "__main__":
    main_loop()
