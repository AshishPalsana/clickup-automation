import requests


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
