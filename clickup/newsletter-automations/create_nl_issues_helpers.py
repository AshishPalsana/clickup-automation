from clickupython import client
from datetime import datetime, timedelta
from pytz import timezone
from clickup_helpers import get_full_task
import calendar
import requests


from config import config

clickup = client.ClickUpClient(config['API_KEY'])


def create_nl_issues(newsletter):
    issues = get_linked_issues(newsletter)
    if issues is not None:
        do_create_issue, most_recent_issue = decide_create_issue(issues)
        if do_create_issue:
            new_issues = process_new_issues(most_recent_issue, newsletter)
            print(f"New issues to be created: {new_issues}")


def get_linked_issues(newsletter):
    # Extract 'Issues' Custom field
    issues_field = next((field for field in newsletter.custom_fields if field.id ==
                        'b181612a-9684-4eeb-9d8e-98d681487d83'), None)
    if issues_field.value is None:
        return None
    # Get each issue task using the ClickUp API
    issue_tasks = [clickup.get_task(issue['id'])
                   for issue in issues_field.value]
    return issue_tasks


def decide_create_issue(issues):
    today = datetime.now().date()
    # Sort issues by due_date in descending order
    sorted_issues = sorted(
        issues, key=lambda issue: issue.due_date, reverse=True)
    # Get the most recent issue
    most_recent_issue = sorted_issues[0]
    # Check if the due_date is beyond a certain date from today
    do_create_issue = datetime.fromtimestamp(int(
        most_recent_issue.due_date) / 1000).date() <= today + timedelta(days=config['lead_time'])
    return do_create_issue, most_recent_issue


def process_new_issues(most_recent_issue, newsletter):
    today = datetime.now().date()

    def string_to_day_of_week(day_str):
        days = ["Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday", "Saturday", "Sunday"]
        return days.index(day_str)

    newsletter = get_full_task(clickup, newsletter.id)
    most_recent_issue = get_full_task(clickup, most_recent_issue.id)

    # Extract 'Cadence' Custom field
    cadence_field = next((field for field in newsletter['custom_fields'] if field['id'] ==
                          'ec92ffcd-9534-4c35-9ee9-bcbc8105eca8'), None)
    # Extract 'Timezone' Custom field
    timezone_field = next((field for field in newsletter['custom_fields'] if field['id'] ==
                           '4c033e84-f88d-4267-bcf4-25d9a8858bec'), None)
    # Extract 'Send Day' Custom field
    send_day_field = next((field for field in newsletter['custom_fields'] if field['id'] ==
                           '25a4d8f7-a735-4bb5-97d6-0fec638eb0bc'), None)
    # Extract 'Send Time' Custom field
    send_time_field = next((field for field in newsletter['custom_fields'] if field['id'] ==
                            '1a056147-ea0a-4650-9a52-5fb4a5fe8fe0'), None)
    # Extract 'Issue Num' Custom field
    issue_num_field = next((field for field in most_recent_issue['custom_fields'] if field['id'] ==
                            '151b839f-2e7f-48ac-8fbd-67018081e4d8'), None)

    # Get the current issue number
    current_issue_num = int(issue_num_field['value'])

    # Convert the timezone string to a pytz timezone object
    timezone_mappings = {
        'Arizona': 'America/Phoenix',
        'PST': 'America/Los_Angeles',
        'CST': 'America/Chicago',
        'MST': 'America/Denver',
        'EST': 'America/New_York'
    }
    current_timezone_str = timezone_field['type_config']['options'][timezone_field['value']]['name']
    current_timezone = timezone(
        timezone_mappings.get(current_timezone_str, 'UTC'))

    # Get the current send day and time
    current_send_day = next((option['label'] for option in send_day_field['type_config']['options']
                            if option['id'] == send_day_field['value'][0]), None) if send_day_field['value'] else None
    current_send_time = next((option['label'] for option in send_time_field['type_config']['options']
                             if option['id'] == send_time_field['value'][0]), None) if send_time_field['value'] else None

    # Parse the send time to a datetime object
    send_time_obj = datetime.strptime(current_send_time, '%H:%M').time()

    # Get the next send date and time
    next_send_date = datetime.now(current_timezone).date()
    next_send_time = send_time_obj

    # Initialize an array to hold the send date and times
    send_date_and_times = []

    # Calculate the next send date and times based on the cadence
    if cadence_field.value == 'Weekly':
        # Calculate the next send date that matches the send day
        days_ahead = (string_to_day_of_week(
            current_send_day) - next_send_date.weekday() + 7) % 7
        next_send_date += timedelta(days=days_ahead)
        # If the send day is less than 3 days from now, schedule for next week
        if days_ahead < config['min_turnaround_days']:
            next_send_date += timedelta(days=7)
        # Add send dates and times for the lead time period
        while next_send_date <= today + timedelta(days=config['lead_time']):
            send_date_and_times.append((next_send_date, next_send_time))
            next_send_date += timedelta(days=7)
    elif cadence_field.value == 'Daily (Excluding Sat & Sun)':
        # Add send dates and times for each weekday in the lead time period
        while next_send_date <= today + timedelta(days=config['lead_time']):
            if next_send_date.weekday() < 5:  # Monday to Friday are 0 to 4
                send_date_and_times.append(
                    (next_send_date, next_send_time))
            next_send_date += timedelta(days=1)
    elif cadence_field.value == 'Daily (Including Sat & Sun)':
        # Add send dates and times for each day in the lead time period
        while next_send_date <= today + timedelta(days=config['lead_time']):
            send_date_and_times.append((next_send_date, next_send_time))
            next_send_date += timedelta(days=1)
    # Other cadences can be added here with their respective logic

    # Create the new issue name
    # Parse the most recent issue name to get the NL name and initial cycle number
    nl_name, _, last_issue_parts = most_recent_issue.name.rpartition(' - ')
    last_issue_cycle_str = last_issue_parts.split('.')[2]  # e.g., "C4"
    last_issue_cycle_num = int(
        last_issue_cycle_str[1:]) if last_issue_cycle_str.startswith('C') else 1

    # Initialize the list to hold new issue creation data
    new_issues_data = []

    # Create the new issue names based on the send date and times
    for send_date, _ in send_date_and_times:
        # Last two digits of the year
        year_short = send_date.strftime('%y')
        # Three-letter month abbreviation
        month_short = send_date.strftime('%b').upper()
        # Check if the month has changed to reset the cycle number
        if send_date.month != current_date.month:
            cycle_num = 1
        else:
            cycle_num = last_issue_cycle_num + 1
        # Increment the current issue number
        current_issue_num += 1
        # Construct the new issue name
        new_issue_name = f"{
            nl_name} - Y{year_short}.{month_short}.C{cycle_num} - Issue {current_issue_num}"
        # Add the new issue data to the list
        new_issues_data.append({'new_issue_name': new_issue_name,
                                'new_issue_num': current_issue_num, 'new_due_date': send_date})
        # Update the last issue cycle number and current date for the next iteration
        last_issue_cycle_num = cycle_num
        current_date = send_date

    # Return the new issue data
    return new_issues_data
