import requests

def get_user_details(user_id, access_token):
    url = f"https://graph.microsoft.com/v1.0/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        return user_data.get("displayName"), user_data.get("mail")
    else:
        return None, None
