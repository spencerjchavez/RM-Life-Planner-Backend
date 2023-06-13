import json
import random
import secrets
import string
import time
import re

import bcrypt
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import Response
import mysql.connector
from mysql.connector import Error

import Routes
from users.UserAsParameter import UserAsParameter
from calendar1.events.CalendarEventsEndpoint import CalendarEventsEndpoint

router = APIRouter()


class UsersEndpoint:
    api_keys_by_userId = {}
    # assumes days are received in terms of epoch-seconds
    API_TIMEOUT_SECS = 60 * 60 * 24  # keep signed in for a day
    try:

        google_db_connection = mysql.connector.connect(
            host='34.31.57.31',
            database='users',
            user='root',
            password='supersecretdatabase$$keepout',
            autocommit=True
        )
        connection = google_db_connection
        users_cursor = connection.cursor(dictionary=True)
        if connection.is_connected():
            print('Connected to users database')
    except Error as e:
        print(f'Error connecting to MySQL database: {e}')

    @staticmethod
    @router.post("/api/users/register")
    def register_user(user: UserAsParameter):
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

        if UsersEndpoint.isUsernameInUse(user.username)["is_in_use"] ==\
                "True":
            print(f"username {user.username} already exists")
            raise HTTPException(detail="Username already in use", status_code=400)
        date_joined = int(time.time())
        # hash password
        password = user.password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
        # insert user into database
        sql = "INSERT INTO users (username, hashed_password, email, date_joined, google_calendar_id, salt) VALUES (%s, %s, %s, %s, %s, %s);"
        UsersEndpoint.users_cursor.execute(sql, (user.username, hashed_password, user.email, date_joined, user.google_calendar_id, salt))

        user_id = UsersEndpoint.users_cursor.lastrowid
        UsersEndpoint.users_cursor.execute(
            f"INSERT INTO user_ids (user_id, username) VALUES (%s, %s);", (user_id, user.username))

        login_res = UsersEndpoint.login_user(user.username, password)
        if login_res[1] != 200:
            print("somethings wrong: user account created but could not be logged in")
            raise HTTPException(detail="user account created, but an internal error prevented it from being logged in!",
                                status_code=500)
        return login_res

    @staticmethod
    @router.get("/api/users/register")
    def isUsernameInUse(username: str):
        UsersEndpoint.users_cursor.execute("SELECT * FROM user_ids WHERE username = %s;", (username,))
        return {"is_in_use": "True" if UsersEndpoint.users_cursor.fetchone() is not None else "False"}

    @staticmethod
    @router.post("/api/users/login")
    def login_user(username: str, password: str):
        UsersEndpoint.users_cursor.execute(f"SELECT * FROM user_ids WHERE username = %s;", (username,))
        res = UsersEndpoint.users_cursor.fetchone()
        if res is None:
            raise HTTPException(detail=username + ": no such user exists", status_code=400)
        user_id = res["user_id"]
        UsersEndpoint.users_cursor.execute(f"SELECT * FROM users WHERE user_id = %s;", (user_id.__str__(),))
        res = UsersEndpoint.users_cursor.fetchone()
        password = password.encode("utf-8")
        salt = res["salt"]
        hashed_password = bcrypt.hashpw(password, salt)
        if res["hashed_password"] == hashed_password:
            #successfully logged in!
            return {"user_id": user_id, "api_key": UsersEndpoint.gen_api_key(user_id)}, 200
        raise HTTPException(status_code=401, detail="username or password is incorrect")

    @staticmethod
    @router.post("/api/users/logout")
    def logout_user(user_id: int, api_key: str):
        if not authenticate(user_id, api_key):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        UsersEndpoint.api_keys_by_userId[user_id] = None
        return "User successfully logged out"

    @staticmethod
    @router.get("/api/users/")
    def get_user(user_id: int, api_key: str):
        if not authenticate(user_id, api_key):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        UsersEndpoint.users_cursor.execute("SELECT * FROM users WHERE user_id = %s;", (user_id.__str__(),))
        user = UsersEndpoint.users_cursor.fetchone()
        if user["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        # Don't return user's salt or hashed_password
        user["salt"] = None
        user["hashed_password"] = None
        return {"message": "successfully got user", "user": json.dumps(user)}, 200

    @staticmethod
    @router.put("/api/users/")
    def update_user(user_id: int, api_key: str, updated_user: UserAsParameter):
        res = UsersEndpoint.get_user(user_id, api_key)
        original_user: UserAsParameter = json.loads(res[0]["user"])
        # make sure the user isn't changing any properties they aren't allowed to
        if updated_user.username != original_user.username:
            raise HTTPException(status_code=401, detail="User is not allowed to access this property")
        UsersEndpoint.users_cursor.execute(f"UPDATE users SET (password = %s, email = %s, google_calendar_id = %s)", (updated_user.password, updated_user.email, updated_user.google_calendar_id))
        return "successfully updated", 200

    @staticmethod
    @router.delete("/api/users/")
    def delete_user(user_id: int, api_key: str):
        if not authenticate(user_id, api_key):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        UsersEndpoint.users_cursor.execute(f"DELETE FROM users WHERE user_id = %s;", (user_id.__str__(),))
        UsersEndpoint.users_cursor.execute(f"DELETE FROM user_ids WHERE user_id = %s;", (user_id.__str__(),))
        try:
            pass
            #TODO: UNCOMMENT THIS OUT WHEN ENDPOINT IS WORKING
            # CalendarEventsEndpoint.delete_events_of_user(user_id, api_key)
        except HTTPException:
            print("Deleted user, but could not delete user events!")
            raise HTTPException(detail="internal error while deleting user", status_code=500)
        del UsersEndpoint.api_keys_by_userId[user_id]
        print("deleted user of id: " + user_id.__str__())
        return "successfully deleted!"

    @staticmethod
    def gen_api_key(user_id: int):
        letters = string.ascii_letters
        api_key = ''.join(random.choice(letters) for _ in range(20))
        UsersEndpoint.api_keys_by_userId[user_id] = {"api_key": api_key, "time_created": time.time()}
        return api_key


def authenticate(user_id: int, api_key: str):
    if user_id is None or api_key is None:
        return False
    print(f"trying to authenticate {user_id} with api_key {api_key}")
    try:
        curr_key = UsersEndpoint.api_keys_by_userId[user_id]
        if curr_key is None:
            return False
        if curr_key['api_key'] == api_key and curr_key['time_created'] + UsersEndpoint.API_TIMEOUT_SECS > time.time():
            # update time_created
            UsersEndpoint.api_keys_by_userId[user_id]['time_created'] = time.time()
            print("user " + user_id.__str__() + " authenticated!")
            return True
    except KeyError:
        # invalid user_id provided
        return False
    print("invalid user_id and api_key combo. Cannot authenticate.")
    return False
