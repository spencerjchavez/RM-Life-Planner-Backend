import datetime
import random
import string
import time
import re

import bcrypt
from fastapi import APIRouter, HTTPException
from mysql.connector import MySQLConnection
from mysql.connector.cursor_cext import CMySQLCursorDict

from app.models.Authentication import Authentication
from app.models.User import User
from app.models.UserPreferences import UserPreferences

router = APIRouter()
cursor: CMySQLCursorDict
db: MySQLConnection


api_keys_by_userId = {}
# assumes days are received in terms of epoch-seconds
API_TIMEOUT_SECS = 60 * 60 * 24  # keep signed in for a day


@router.post("/api/users/register")
def register_user(user: User):
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

    if is_username_in_use(user.username)["is_in_use"] ==\
            "True":
        raise HTTPException(detail="Username already in use", status_code=400)
    date_joined = datetime.datetime.now().strftime("%Y-%m-%d")
    # hash password
    password = user.password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

    user.dateJoined = date_joined
    user.hashedPassword = hashed_password

    # insert user into database
    stmt = user.get_sql_insert_query()
    params = user.get_sql_insert_params()
    cursor.execute(stmt, params)
    _ = cursor.fetchone()

    # init user preferences
    user_preferences = UserPreferences(
        userId=cursor.lastrowid,
        highestPriorityColor="0xFFFFFF",
        veryHighPriorityColor="0xFFFFFF",
        highPriorityColor="0xFFFFFF",
        mediumPriorityColor="0xFFFFFF",
        lowPriorityColor="0xFFFFFF",
    )
    cursor.execute(user_preferences.get_sql_events_insert_query(), user_preferences.get_sql_insert_params())
    
    return login_user(user.username, password)


@router.get("/api/users/register")
def is_username_in_use(username: str):
    cursor.execute("SELECT * FROM users WHERE username = %s;", (username,))
    return {"is_in_use": "True" if cursor.fetchone() is not None else "False"}


@router.post("/api/users/login")
def login_user(username: str, password: str):
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    res = cursor.fetchone()
    if res is None:
        raise HTTPException(status_code=404, detail="username or password is incorrect")
    password = password.encode("utf-8")
    if bcrypt.checkpw(password, res["hashed_password"]):
        #successfully logged in!
        user_id = res["user_id"]
        cursor.execute("SELECT * FROM user_preferences WHERE user_id = %s", (user_id,))
        res = cursor.fetchone()
        if res is None:
            raise HTTPException(status_code=404, detail="could not find user preferences for the given user!")
        user_preferences = UserPreferences.from_sql_res(res)
        return {"authentication": gen_api_key(user_id), "user_preferences": user_preferences}
    raise HTTPException(status_code=401, detail="username or password is incorrect")


@router.post("/api/users/logout/{user_id}")
def logout_user(user_id: int, authentication: Authentication):
    user_id = authentication.user_id
    if not authenticate(authentication):
        raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
    api_keys_by_userId[user_id] = None
    
    return "User successfully logged out"


@router.get("/api/users/{user_id}")
def get_user(auth_user: int, api_key: str, user_id: int):
    user_id = auth_user
    authentication = Authentication(user_id, api_key)
    if not authenticate(authentication):
        raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
    cursor.execute("SELECT * FROM users WHERE user_id = %s;", (user_id,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(detail="specified user does not exist", status_code=404)
    if user["user_id"] != user_id or authentication.user_id != user_id:
        raise HTTPException(status_code=401, detail="User is not authenticated to access this resource")
    return {"message": "successfully got user", "user": User.from_sql_res(user)}


def get_user_with_login_info(user_id: int):
    cursor.execute("SELECT * FROM users WHERE user_id = %s;", (user_id,))
    return cursor.fetchone()


@router.put("/api/users/{user_id}")
def update_user(authentication: Authentication, user_id: int, updated_user: User):
    if not authenticate(authentication):
        raise HTTPException(status_code=401, detail="User could not be authenticatied, please log in")
    res = get_user_with_login_info(user_id)
    updated_user.userId = user_id
    if updated_user.password is not None:
        salt = bcrypt.gensalt()
        updated_user.hashedPassword = bcrypt.hashpw(updated_user.password.encode("utf-8"), salt)
    else:
        updated_user.hashedPassword = res["hashed_password"]
    updated_user.dateJoined = res["date_joined"]
    __validate_user(updated_user)
    cursor.execute("UPDATE users SET hashed_password = %s, email = %s, google_calendar_id = %s WHERE user_id = %s;",
                   (updated_user.hashedPassword,
                    updated_user.email,
                    updated_user.googleCalendarId,
                    user_id))
    
    return "successfully updated"


@router.delete("/api/users/{user_id}")
def delete_user(auth_user: int, api_key: str, user_id: int):
    user_id = auth_user
    if not authenticate(Authentication(auth_user, api_key)):
        raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
    cursor.execute("DELETE FROM alerts WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM months_accessed_by_user WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM events WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM todos WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM goals WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM desires WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    del api_keys_by_userId[user_id]
    print("deleted user of id: " + user_id.__str__())
    
    return "successfully deleted!"


def gen_api_key(user_id: int):
    letters = string.ascii_letters
    api_key = ''.join(random.choice(letters) for _ in range(50))
    api_keys_by_userId[user_id] = {"api_key": api_key, "time_created": time.time()}
    return Authentication(user_id=user_id, api_key=api_key)


def authenticate(authentication: Authentication):
    user_id = authentication.user_id
    api_key = authentication.api_key

    if user_id is None or api_key is None:
        return False
    try:
        curr_key = api_keys_by_userId[user_id]
        if curr_key is None:
            return False
        if curr_key['api_key'] == api_key and curr_key['time_created'] + API_TIMEOUT_SECS > time.time():
            # update time_created
            api_keys_by_userId[user_id]['time_created'] = time.time()
            return True
    except KeyError:
        # invalid user_id provided
        return False
    return False


def __validate_user(user: User):
    if user.userId is None:
        raise HTTPException(detail="user must define a user id", status_code=400)
    if user.username is None:
        raise HTTPException(detail="user must define a username", status_code=400)
    if len(user.username) == 0 or len(user.username) > 24:
        raise HTTPException(detail="user must define a username between 1 and 24 characters long", status_code=400)
    if user.hashedPassword is None:
        raise HTTPException(detail="user must define a password", status_code=400)
    if user.dateJoined is None:
        raise HTTPException(detail="user must define a date joined attribute", status_code=400)
    if user.email is None:
        raise HTTPException(detail="user must define a valid email", status_code=400)
    if len(user.email) <= 4 or len(user.email) > 42:
        raise HTTPException(detail="user's email must be less than 42 characters long", status_code=400)
