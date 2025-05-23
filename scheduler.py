from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from src.database.mongodb import db
from datetime import datetime
import requests
import sqlite3  # or use your actual DB module
import time

# Configuration
API_ENDPOINT = "http://127.0.0.1:8000/launch/execute_call_batch"

# Function to trigger API
def trigger_api(batch_name, user_id):
    print(f"Triggering API for {batch_name} at {datetime.now()}")
    response = requests.post(API_ENDPOINT, json={"batch_name": batch_name, "user_id": user_id})
    print(f"Status: {response.status_code}, Response: {response.text}")

# Load jobs from database
def load_scheduled_jobs(scheduler):
    batch_details = list(db.call_batch_details.find())

    for batch_detail in batch_details:
        kick_time = batch_detail['scheduledTime']
        if kick_time >= datetime.now():
            batch_name = batch_detail['batch_name']
            user_id = batch_detail['created_by']
            scheduler.add_job(trigger_api, 'date', run_date=kick_time, args=[batch_name, user_id], id=batch_name)


# Setup scheduler
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')  # Persists scheduled jobs
}
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

# Load jobs from DB
load_scheduled_jobs(scheduler)

# Keep script running
try:
    while True:
        time.sleep(5)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
