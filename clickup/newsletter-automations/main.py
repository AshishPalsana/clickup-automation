import requests
from clickupython import client
from datetime import datetime, timedelta
from pytz import timezone
import calendar
from create_nl_issues_helpers import create_nl_issues
from config import config
from clickup_helpers import update_due_date


clickup = client.ClickUpClient(config['API_KEY'])


def parse_request(request):
    request_json = request.get_json(silent=True)
    print(f"Request json: {request_json}")
    action = request_json.get('action')

    try:
        match action:
            case "scheduled_issue_update":
                scheduled_issue_update()
            case _:
                print(f"Unknown action: {action}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return


def scheduled_issue_update():

    newsletters = clickup.get_tasks(config['NEWSLETTER_LIST_ID'])

    for newsletter in newsletters:

        create_nl_issues(newsletter)

def single_issue_creation(type):
    #if type is prototype issue, then do prototype things
    # otherwise just create the first issue
    pass

def change_dates(request):
    # move dates forward or backwards on the singlue issue
    request_json = request.get_json(silent=True)
    print(f"Request json: {request_json}")
    task_id = request_json.get('task_id')
    days = request_json.get('days')

    task = clickup.get_task(task_id)
    task_duedate = task.due_date

    return update_due_date(task_id,task_duedate,days)

if __name__ == "__main__":
    class FakeRequest:
        def get_json(self, silent=False):
            return {"action": "scheduled_issue_update", "data": {}}

    fake_request = FakeRequest()

    parse_request(fake_request)

