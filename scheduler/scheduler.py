
import os
import time
import threading
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

FUZZY_SERVICE_URL = "http://fuzzy_service:5000"
SENTIMENT_SERVICE_URL = "http://sentiment_service:5000"
API_KEY = os.getenv("FUZZY_API_KEY")

INTERVAL = 3 * 60
JAKARTA = ZoneInfo("Asia/Jakarta")
DAILY_RUN_TIME = "17:00"

def get_headers():
    return {"X-API-Key": API_KEY}

def post_service(name, url, timeout=1800, params=None):
    now = datetime.now(JAKARTA)
    print("=" * 60)
    print(f"[{now:%Y-%m-%d %H:%M:%S}] Memulai {name}...")
    print("=" * 60)

    try:
        response = requests.post(
            url,
            headers=get_headers(),
            params=params,
            timeout=timeout
        )
        print(f"Status HTTP: {response.status_code}")
        response.raise_for_status()

        try:
            result = response.json()
            print(f"Status: {result.get('status', '-')}")
            print(f"Pesan: {result.get('message', '-')}")
            if "total" in result:
                print(f"Total saham: {result['total']}")
            if "total_berita" in result:
                print(f"Total berita: {result['total_berita']}")
            if "berita_baru" in result:
                print(f"Berita baru: {result['berita_baru']}")
            print(f"Respons: {result}")
        except ValueError:
            print(response.text)

        return True

    except requests.Timeout:
        print(f"ERROR {name}: Request timeout.")
    except requests.HTTPError as e:
        print(f"ERROR {name} HTTP: {e}")
        if e.response is not None:
            print(f"Respons: {e.response.text[:1000]}")
    except requests.RequestException as e:
        print(f"ERROR koneksi {name}: {e}")
    except Exception as e:
        print(f"ERROR {name}: {e}")

    return False

def run_realtime():
    return post_service(
        "realtime recommendation",
        f"{FUZZY_SERVICE_URL}/realtime/run"
    )

def run_sentiment():
    return post_service(
        "realtime sentiment",
        f"{SENTIMENT_SERVICE_URL}/sentiment/run"
    )

def run_stock_fetch():
    return post_service(
        "pengambilan data saham harian",
        f"{FUZZY_SERVICE_URL}/stock/fetch",
        params={"mode": "daily"}
    )

def run_fuzzy():
    return post_service(
        "perhitungan fuzzy harian",
        f"{FUZZY_SERVICE_URL}/fuzzy/run"
    )

def run_daily_pipeline():
    now = datetime.now(JAKARTA)
    print("\n" + "#" * 60)
    print(f"[{now:%Y-%m-%d %H:%M:%S}] PIPELINE HARIAN 17.00 WIB")
    print("#" * 60)
    if not run_stock_fetch():
        print("Pipeline dihentikan: stock fetch gagal.")
        return
    if not run_fuzzy():
        print("Pipeline selesai dengan kegagalan pada fuzzy run.")
        return

    print("Pipeline harian selesai dengan sukses.")

def daily_scheduler():
    last_run_date = None

    while True:
        try:
            now = datetime.now(JAKARTA)
            today = now.date()

            if (
                now.strftime("%H:%M") >= DAILY_RUN_TIME
                and last_run_date != today
            ):
                # Tandai tanggal agar tidak dipanggil berulang
                last_run_date = today
                run_daily_pipeline()

        except Exception as e:
            print(f"ERROR daily scheduler: {e}")

        time.sleep(10)


if __name__ == "__main__":
    print("=" * 60)
    print("REALTIME STOCK SCHEDULER")
    print("Sentiment: Setiap hari, setiap 3 menit")
    print("Daily Trading: Senin-Jumat")
    print("Sesi 1: 09.00 - 12.30 WIB")
    print("Sesi 2: 13.45 - 16.30 WIB")
    print("Stock Fetch + Fuzzy: Hari kerja pukul 17.00 WIB")
    print("=" * 60)

    daily_thread = threading.Thread(
        target=daily_scheduler,
        daemon=True
    )
    daily_thread.start()

    while True:
        now = datetime.now(JAKARTA)
        current_time = now.strftime("%H:%M")
        weekday = now.weekday() < 5

        # SENTIMENT TETAP BERJALAN SETIAP HARI
        run_sentiment()

        # DAILY TRADING HANYA SENIN-JUMAT
        if weekday:
            sesi_1 = "09:00" <= current_time < "12:30"
            sesi_2 = "13:45" <= current_time < "16:30"

            if sesi_1 or sesi_2:
                run_realtime()
            else:
                print(
                    f"[{now:%Y-%m-%d %H:%M:%S}] "
                    "Daily trading berhenti di luar jam sesi."
                )
        else:
            print(
                f"[{now:%Y-%m-%d %H:%M:%S}] "
                "Akhir pekan: hanya sentiment yang berjalan."
            )

        print(f"\nMenunggu {INTERVAL // 60} menit...")
        time.sleep(INTERVAL)
