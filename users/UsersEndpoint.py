import json
import random
import secrets
import string
import time

import bcrypt
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import mysql.connector
from mysql.connector import Error

import Routes
from users.UserAsParameter import UserAsParameter
from users.User import User
from calendar1.events import CalendarEventsEndpoint

router = APIRouter()


class UsersEndpoint:
    api_keys_by_userId = {}
    # assumes days are received in terms of epoch-seconds
    API_TIMEOUT_SECS = 60 * 60 * 24  # keep signed in for a day
    try:
        connection = mysql.connector.connect(
            host='34.31.57.31',
            database='users',
            user='root',
            password='supersecretdatabase$$keepout',
            autocommit=True
        )
        users_cursor = connection.cursor(dictionary=True)
        if connection.is_connected():
            print('Connected to users database')
    except Error as e:
        print(f'Error connecting to MySQL database: {e}')

    @staticmethod
    @router.post("/api/users/register")
    def register_user(user_param: UserAsParameter):
        # check if username is in use
        # user = json.load(user, User)
        if UsersEndpoint.isUsernameInUse(user_param.username)["is_in_use"] == "True":
            print(f"username {user_param.username} already exists")
            raise HTTPException(detail="Username already in use", status_code=400)
        # generate a unique user_id, of size int (4 bytes), with the 4th byte set to 10000000. user_id will be 10 digits long in base10
        UsersEndpoint.users_cursor.execute("SELECT MAX(user_id) FROM users;")
        user = User(username=user_param.username, email=user_param.email,
                    google_calendar_id=user_param.google_calendar_id)
        max_id = UsersEndpoint.users_cursor.fetchone()["MAX(user_id)"]
        if max_id is None:
            max_id = 0
        user.user_id = max_id + 1
        UsersEndpoint.users_cursor.execute(
            f"INSERT INTO user_ids (user_id, username) VALUES (%s, %s);", (user.user_id.__str__(), user.username))

        user.date_joined = int(time.time())
        # hash password
        password = user_param.password
        user.salt = bcrypt.gensalt()
        user.hashed_password = bcrypt.hashpw(password.encode("utf-8"), user.salt)
        # insert user into database
        sql = "INSERT INTO users (username, hashed_password, user_id, email, date_joined, google_calendar_id, salt) VALUES (%s, %s, %s, %s, %s, %s, %s);"
        UsersEndpoint.users_cursor.execute(sql,(user.username, user.hashed_password, user.user_id, user.email, user.date_joined, user.google_calendar_id, user.salt))

        login_res = UsersEndpoint.loginUser(user.username, password)
        if login_res[0] != 200:
            print("somethings wrong: user account created but could not be logged in")
            raise HTTPException(detail="user account created, but an internal error prevented it from being logged in!",
                                status_code=400)
        return login_res

    @staticmethod
    @router.get("/api/users/register")
    def isUsernameInUse(username: str):
        UsersEndpoint.users_cursor.execute("SELECT * FROM user_ids WHERE username = %s;", (username,))
        return {"is_in_use": "True" if UsersEndpoint.users_cursor.fetchone() is not None else "False"}

    @staticmethod
    @router.post("/api/users/users")
    def loginUser(username: str, password: str):
        UsersEndpoint.users_cursor.execute(f"SELECT * FROM user_ids WHERE username = %s;", (username,))
        if len(UsersEndpoint.users_cursor.fetchall()) == 0:
            raise HTTPException(detail=username + ": no such user exists", status_code=400)
        user_id = UsersEndpoint.users_cursor.fetchall()["user_id"]
        UsersEndpoint.users_cursor.execute(f"SELECT * FROM users WHERE user_id = %s;", (user_id.__str__(),))
        res = UsersEndpoint.users_cursor.fetchone()
        password = password.encode("utf-8")
        salt = res["salt"]
        hashed_password = bcrypt.hashpw(password, salt)
        if res["hashed_password"] == hashed_password:
            return Response({"api_key": UsersEndpoint.gen_api_key(user_id)}, 200)

    @staticmethod
    @router.delete("/api/users/logout")
    def logoutUser(user_id: int, api_key: str):
        if not authenticate(user_id, api_key):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        UsersEndpoint.api_keys_by_userId[user_id] = None
        return "User successfully logged out"

    @staticmethod
    @router.get("/api/users")
    def getUser(user_id: int, api_key: str):
        if not authenticate(user_id, api_key):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        UsersEndpoint.users_cursor.execute("SELECT * FROM users WHERE user_id = %s;", (user_id.__str__(),))
        print("got user: " + UsersEndpoint.users_cursor.fetchone()["user_id"])
        return {"user_id": UsersEndpoint.users_cursor()["user_id"]}, 200

    @staticmethod
    @router.delete("api/users")
    def delete_user(user_id: int, api_key: str):
        if not authenticate(user_id, api_key):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        UsersEndpoint.users_cursor.execute(f"DELETE * FROM users WHERE user_id = %s;", (user_id.__str__(),))
        UsersEndpoint.users_cursor.execute(f"DELETE * FROM user_ids WHERE user_id = %s;", (user_id.__str__(),))
        UsersEndpoint.api_keys_by_userId[user_id] = None
        if CalendarEventsEndpoint.delete_events_of_user(user_id, api_key).status_code != 200:
            print("Deleted user, but could not delete user events!")
            raise HTTPException(detail="internal error while deleting user", status_code=500)
        print("deleted user of id: " + user_id.__str__())
        return Response()

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
    curr_key = UsersEndpoint.api_keys_by_userId.get(user_id.__str__())
    if curr_key is None:
        return False
    if curr_key['key'] == api_key and curr_key['time_created'] + UsersEndpoint.API_TIMEOUT_SECS > time.time():
        UsersEndpoint.api_keys_by_userId[user_id]['time_created'] = time.time()
        print("user " + user_id.__str__() + " authenticated!")
        return True
    print("invalid user_id and api_key combo. Cannot authenticate.")
    return False
