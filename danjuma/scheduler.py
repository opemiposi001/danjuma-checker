from apscheduler.schedulers.background import BackgroundScheduler
from services.scanner import run_scan_for_all_registered_emails

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_scan_for_all_registered_emails, 'interval', minutes=5)
    scheduler.start()
    print("Background scheduler started...")
