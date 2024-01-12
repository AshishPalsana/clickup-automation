from datetime import datetime, timedelta
import requests
from flask import render_template_string
from config import config

def get_full_task(clickup, task_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": clickup.accesstoken
    }
    url = "https://api.clickup.com/api/v2/task/" + \
        task_id
    query = {
    }
    response = requests.get(url, headers=headers, params=query)
    data = response.json()
    return data

def create_task(clickup,list_id,name,parent_task_id):
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"

    headers = {
        "Content-Type": "application/json",
        "Authorization": clickup.accesstoken
    }

    data = {
      "name": name,
      "description": "New Task Description",
      "assignees": [],
      "tags": [],
      "status": "Open",
      "priority": None,
      "due_date": None,
      "due_date_time": None,
      "time_estimate": None,
      "start_date": None,
      "start_date_time": None,
      "notify_all": None,
      "parent": None,
      "links_to": parent_task_id,
      "custom_fields": []
    }

    res = requests.post(url,headers=headers,json=data)
    return res.json()

def update_due_date(task_id,task_duedate,days):

    # Given timestamp in milliseconds
    timestamp_ms = int(task_duedate)

    # Convert milliseconds to seconds by dividing by 1000
    timestamp_seconds = timestamp_ms / 1000

    # Create a datetime object from the timestamp
    datetime_obj = datetime.fromtimestamp(timestamp_seconds)

    # Add 7 days using timedelta
    datetime_after_n_days = datetime_obj + timedelta(days=days)

    # Convert the updated datetime object to a timestamp in milliseconds
    timestamp_after_n_days_ms = int(datetime_after_n_days.timestamp() * 1000)

    url = "https://api.clickup.com/api/v2/task/" + task_id

    payload = {
        "id": task_id,
        "due_date": timestamp_after_n_days_ms
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": F"{config['API_KEY']}"
    }

    response = requests.put(url, json=payload, headers=headers)

    return render_template_string('''<script>window.close();</script>''')
