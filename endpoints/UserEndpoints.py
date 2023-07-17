import json
import random
import string
import time
import re

import bcrypt
from fastapi import APIRouter, HTTPException
from mysql.connector.connection import MySQLCursor
from models.Authentication import Authentication
from endpoints.CalendarEventEndpoints import CalendarEventEndpoints

from models.User import User


class UserEndpoints:
    router = APIRouter()
    cursor: MySQLCursor
    
    api_keys_by_userId = {}
    # assumes days are received in terms of epoch-seconds
    API_TIMEOUT_SECS = 60 * 60 * 24  # keep signed in for a day
    
    @staticmethod
    @router.post("/api/users/register")
    def register_user(user: User):
        # check if username is in use
        # user = json.load(user, User)
        if user.username is None:
            raise HTTPException(detail="Username too short", status_code=400)
        if user.password is None:
            raise HTTPException(detail="Password too short", status_code=400)
        if len(user.username) <= 3:
            raise HTTPException(detail="Username too short", status_code=400)
        if len(user.username) > 24:
            raise HTTPException(detail="Username must be 24 characters or less", status_code=400)
        exp = r'[^\w\s\$\#\&\!\?\@]'
        if re.search(exp, user.username) is not None:
            raise HTTPException(
                detail="Username may only contain digits, letters, and these characters: !, ? @, #, $, &",
                status_code=400)
        if len(user.password) <= 7:
            raise HTTPException(detail="Password too short", status_code=400)
        if re.search(exp, user.password) is not None:
            raise HTTPException(detail="Password may only contain digits, letters, and these characters: !, ? @, #, $, &", status_code=400)
        if len(user.password) > 32:
            raise HTTPException(detail="Password must be 32 characters or less", status_code=400)

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if user.email is not None:
            if re.match(email_pattern, user.email) is None:
                raise HTTPException(detail="Must enter a valid email address!", status_code=400)

        if UserEndpoints.isUsernameInUse(user.username)["is_in_use"] ==\
                "True":
            print(f"username {user.username} already exists")
            raise HTTPException(detail="Username already in use", status_code=400)
        date_joined = int(time.time())
        # hash password
        password = user.password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
        # insert user into database
        stmt = user.get_sql_insert_query()
        params = user.get_sql_insert_params()
        UserEndpoints.cursor.execute(stmt, params)
        user_id = UserEndpoints.cursor.lastrowid

        login_res = UserEndpoints.login_user(user.username, password)
        if login_res[1] != 200:
            print("somethings wrong: user account created but could not be logged in")
            raise HTTPException(detail="user account created, but an internal error prevented it from being logged in!",
                                status_code=500)
        return login_res

    @staticmethod
    @router.get("/api/users/register")
    def is_username_in_use(username: str):
        UserEndpoints.cursor.execute("SELECT * FROM users WHERE username = %s;", (username,))
        return 200, {"is_in_use": "True" if UserEndpoints.cursor.fetchone() is not None else "False"}

    @staticmethod
    @router.post("/api/users/login")
    def login_user(username: str, password: str):
        UserEndpoints.cursor.execute("SELECT * FROM users WHERE username = %s;", (username,))
        res = UserEndpoints.cursor.fetchone()
        password = password.encode("utf-8")
        salt = res["salt"]
        hashed_password = bcrypt.hashpw(password, salt)
        if res["hashed_password"] == hashed_password:
            #successfully logged in!
            return {"authentication": UserEndpoints.gen_api_key(res["user_id"])}, 200
        raise HTTPException(status_code=401, detail="username or password is incorrect")

    @staticmethod
    @router.post("/api/users/logout/{user_id}")
    def logout_user(authentication: Authentication, user_id: int):
        user_id = authentication.user_id
        if not authenticate(authentication):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        UserEndpoints.api_keys_by_userId[user_id] = None
        return "User successfully logged out"

    @staticmethod
    @router.get("/api/users/{user_id}")
    def get_user(authentication: Authentication, user_id):
        user_id = authentication.user_id
        if not authenticate(authentication):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        UserEndpoints.cursor.execute("SELECT * FROM users WHERE user_id = %s;", (user_id.__str__(),))
        user = UserEndpoints.cursor.fetchone()
        if user["user_id"] != user_id or authentication.user_id != user_id:
            raise HTTPException(status_code=401, detail="User is not authenticated to access this resource")
        # Don't return user's salt or hashed_password
        user["salt"] = None
        user["hashed_password"] = None
        return {"message": "successfully got user", "user": user}, 200

    @staticmethod
    @router.put("/api/users/{user_id}")
    def update_user(authentication: Authentication, user_id: int, updated_user: User):
        res = UserEndpoints.get_user(authentication)
        original_user_dict = res[0]["user"]
        # make sure the user isn't changing any properties they aren't allowed to
        UserEndpoints.cursor.execute("UPDATE users SET (password = %s, email = %s, google_calendar_id = %s)", (updated_user.password, updated_user.email, updated_user.googleCalendarId))
        return "successfully updated", 200

    @staticmethod
    @router.delete("/api/users/{user_id}")
    def delete_user(authentication: Authentication, user_id: int):
        user_id = authentication.user_id
        if not authenticate(authentication):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        UserEndpoints.cursor.execute("DELETE FROM actions WHERE user_id = %s", (user_id,))
        UserEndpoints.cursor.execute("DELETE FROM plans WHERE user_id = %s", (user_id,))
        UserEndpoints.cursor.execute("DELETE FROM todos_in_day WHERE user_id = %s", (user_id,))
        UserEndpoints.cursor.execute("DELETE FROM todos WHERE user_id = %s", (user_id,))
        UserEndpoints.cursor.execute("DELETE FROM events_in_day WHERE user_id = %s", (user_id,))
        UserEndpoints.cursor.execute("DELETE FROM events WHERE user_id = %s", (user_id,))
        UserEndpoints.cursor.execute("DELETE FROM alerts WHERE user_id = %s", (user_id,))
        UserEndpoints.cursor.execute("DELETE FROM goals WHERE user_id = %s", (user_id,))
        UserEndpoints.cursor.execute("DELETE FROM recurrences WHERE user_id = %s", (user_id,))
        UserEndpoints.cursor.execute("DELETE FROM desires WHERE user_id = %s", (user_id,))
        UserEndpoints.cursor.execute("DELETE FROM months_accessed_by_user WHERE user_id = %s", (user_id,))
        UserEndpoints.cursor.execute("DELETE FROM users WHERE user_id = %s;", (user_id,))
        del UserEndpoints.api_keys_by_userId[user_id]
        print("deleted user of id: " + user_id.__str__())
        return 200, "successfully deleted!"

    @staticmethod
    def gen_api_key(user_id: int):
        letters = string.ascii_letters
        api_key = ''.join(random.choice(letters) for _ in range(50))
        UserEndpoints.api_keys_by_userId[user_id] = {"api_key": api_key, "time_created": time.time()}
        return Authentication(user_id=user_id, api_key=api_key)


def authenticate(authentication: Authentication):
    user_id = authentication.user_id
    api_key = authentication.api_key

    if user_id is None or api_key is None:
        return False
    print(f"trying to authenticate {user_id} with api_key {api_key}")
    try:
        curr_key = UserEndpoints.api_keys_by_userId[user_id]
        if curr_key is None:
            return False
        if curr_key['api_key'] == api_key and curr_key['time_created'] + UserEndpoints.API_TIMEOUT_SECS > time.time():
            # update time_created
            UserEndpoints.api_keys_by_userId[user_id]['time_created'] = time.time()
            print("user " + user_id.__str__() + " authenticated!")
            return True
    except KeyError:
        # invalid user_id provided
        return False
    print("invalid user_id and api_key combo. Cannot authenticate.")
    return False