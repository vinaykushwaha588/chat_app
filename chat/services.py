import json
from uuid import UUID
import requests
from .models import FakeUserData


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj) 
        return super().default(obj)



def fetch_and_store_users():
    try:
        API_URL = "https://dummyjson.com/users"
        response = requests.get(API_URL)

        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])  
            
            for user in users:
                FakeUserData.objects.update_or_create(
                    id=user["id"], 
                    defaults={
                        "first_name": user["firstName"],
                        "last_name": user["lastName"],
                        "email": user["email"],
                        "phone": user["phone"],
                        "age": user["age"],
                        "gender": user["gender"],
                    }
                )
            print("User data stored successfully!")

        else:
            print("Error: Received status code", response.status_code)

    except Exception as err:
        print("Error Occurred:", str(err))
