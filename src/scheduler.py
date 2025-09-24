
import schedule
import time
from src.core.app import run_trading_app

def main():
    schedule.every().day.at("09:30").do(run_trading_app)
    print("Scheduler started. Waiting for next run...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
