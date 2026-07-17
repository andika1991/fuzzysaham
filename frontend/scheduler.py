import threading
import schedule
import time
import requests

def auto_job():

    print("=== AUTO UPDATE ===")

    try:

        requests.get(
            "http://frontend:5000/stock/fetch",
            timeout=600
        )

        requests.get(
            "http://sentiment_service:5000/sentiment/run",
            timeout=600
        )

        requests.get(
            "http://fuzzy_service:5000/fuzzy/run",
            timeout=600
        )

        print("=== UPDATE SELESAI ===")

    except Exception as e:
        print("Scheduler Error :", e)


def run_scheduler():

    # setiap hari jam 17:05 WIB
    schedule.every().day.at("17:05").do(auto_job)

    while True:
        schedule.run_pending()
        time.sleep(30)


def start_scheduler():
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()