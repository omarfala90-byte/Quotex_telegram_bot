import os
import time
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is missing")

if not TWELVE_DATA_API_KEY:
    raise ValueError("TWELVE_DATA_API_KEY is missing")

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_URL}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": text
        },
        timeout=20
    )


def get_market_data(symbol):
    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": "1min",
        "outputsize": 30,
        "apikey": TWELVE_DATA_API_KEY
    }

    response = requests.get(url, params=params, timeout=20)
    data = response.json()

    if "values" not in data:
        return None, data.get("message", "تعذر الحصول على البيانات")

    values = data["values"]

    closes = [float(x["close"]) for x in values]
    closes.reverse()

    return closes, None


def calculate_signal(closes):
    if len(closes) < 20:
        return "NEUTRAL", "البيانات غير كافية للتحليل."

    short_avg = sum(closes[-5:]) / 5
    long_avg = sum(closes[-20:]) / 20

    current_price = closes[-1]

    if short_avg > long_avg and current_price > long_avg:
        signal = "UP 📈"
        explanation = "المتوسط القصير أعلى من المتوسط الطويل."
    elif short_avg < long_avg and current_price < long_avg:
        signal = "DOWN 📉"
        explanation = "المتوسط القصير أسفل المتوسط الطويل."
    else:
        signal = "NEUTRAL ⚪"
        explanation = "الإشارة غير واضحة حالياً."

    return signal, explanation


def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if text == "/start":
        send_message(
            chat_id,
            "🤖 مرحباً بك في Market Analyzer\n\n"
            "أرسل:\n"
            "/signal EUR/USD\n\n"
            "مثال آخر:\n"
            "/signal BTC/USD"
        )
        return

    if text.startswith("/signal"):
        parts = text.split()

        if len(parts) != 2:
            send_message(
                chat_id,
                "❌ الصيغة الصحيحة:\n/signal EUR/USD"
            )
            return

        symbol = parts[1].upper()

        send_message(
            chat_id,
            f"🔎 جاري تحليل {symbol}..."
        )

        closes, error = get_market_data(symbol)

        if error:
            send_message(
                chat_id,
                f"❌ حدث خطأ:\n{error}"
            )
            return

        signal, explanation = calculate_signal(closes)

        price = closes[-1]

        result = (
            f"📊 Market Analyzer\n\n"
            f"💱 الأصل: {symbol}\n"
            f"💰 السعر: {price}\n\n"
            f"🎯 الإشارة: {signal}\n\n"
            f"📌 التحليل: {explanation}\n\n"
            f"⚠️ هذه إشارة تحليلية وليست ضماناً لنتيجة الصفقة."
        )

        send_message(chat_id, result)
        return

    send_message(
        chat_id,
        "❓ الأمر غير معروف.\n\n"
        "استخدم:\n"
        "/signal EUR/USD"
    )


def main():
    print("🤖 Telegram Market Analyzer is running...")

    offset = 0

    while True:
        try:
            response = requests.get(
                f"{TELEGRAM_URL}/getUpdates",
                params={
                    "offset": offset,
                    "timeout": 30
                },
                timeout=40
            )

            data = response.json()

            if not data.get("ok"):
                time.sleep(5)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                if "message" in update:
                    handle_message(update["message"])

        except Exception as e:
            print("Error:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
