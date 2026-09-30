import os
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


FUZZY_SERVICE_URL = "http://fuzzy_service:5000"
SENTIMENT_SERVICE_URL = "http://sentiment_service:5000"


API_KEY = os.getenv("FUZZY_API_KEY")

INTERVAL = 3 * 60

def run_realtime():

    url = f"{FUZZY_SERVICE_URL}/realtime/run"

    headers = {
        "X-API-Key": API_KEY
    }

    try:

        now = datetime.now(
            ZoneInfo("Asia/Jakarta")
        )

        print("=" * 60)

        print(
            f"[{now:%Y-%m-%d %H:%M:%S}] "
            "Memulai realtime recommendation..."
        )

        print("=" * 60)

        response = requests.post(
            url,
            headers=headers,
            timeout=1800
        )

        print(
            f"Status HTTP: "
            f"{response.status_code}"
        )

        try:

            result = response.json()

            print(
                f"Status: "
                f"{result.get('status')}"
            )

            print(
                f"Total saham: "
                f"{result.get('total')}"
            )

        except Exception:

            print(
                response.text
            )

    except Exception as e:

        print(
            f"❌ ERROR scheduler: {e}"
        )

def run_sentiment():

    url = f"{SENTIMENT_SERVICE_URL}/sentiment/run"

    headers = {
        "X-API-Key": API_KEY
    }

    try:

        now = datetime.now(
            ZoneInfo("Asia/Jakarta")
        )

        print("=" * 60)

        print(
            f"[{now:%Y-%m-%d %H:%M:%S}] "
            "Memulai realtime sentiment..."
        )

        print("=" * 60)

        response = requests.post(
            url,
            headers=headers,
            timeout=1800
        )

        print(
            f"Status HTTP: "
            f"{response.status_code}"
        )

        try:

            result = response.json()

            print(
                f"Status: "
                f"{result.get('status')}"
            )

        except Exception:
            print(
                response.text
            )
    except Exception as e:
        print(
            f"❌ ERROR scheduler: {e}"
        )


if __name__ == "__main__":

    print("=" * 60)
    print("REALTIME STOCK SCHEDULER")
    print("Interval: 17 menit")
    print("=" * 60)

    while True:
        run_sentiment()
        run_realtime()
        print(
            f"\n⏳ Menunggu "
            f"{INTERVAL // 60} menit..."
        )

        time.sleep(
            INTERVAL
        )