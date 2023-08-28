from app.models.User import User

USER1 = User(
    username="user1",
    password="passwordpassword",
    email="email@realemail.com",
    googleCalendarId="google_calendar_id321"
)

USER2 = User(
    username="user2",
    password="passwordpassword",
    email="user2@realemail.com"
)

USER3 = User(
    username="user3",
    password="passwordpassword",
    email="iamuser3@gmail.com",
    googleCalendarId="google_calendar_id32100123"
)

INVALID_USER1 = User(
username="",
password="passwordpassword",
email="email@realemail.com"
)
INVALID_USER2 = User(
    username="a",
    password="",
    email="email@realemail.com"
)
INVALID_USER2_REPEAT = User(
    username="user2",
    password="passwordpassword",
    email="email@realemail.com"
)
INVALID_USER3 = User(
    username="hellow babay",
    password="passwordpassword**",
    email="email@realemail.com"
)
INVALID_USER4 = User(
    password="passwordpassword",
    email="email@realemail.com"
)
INVALID_USER5 = User(
    username="ueao",
    email="email@realemail.com"
)
INVALID_USER6 = User(
    username="unique",
    password="2short",
    email="email@realemail.com"
)
INVALID_USER7=User(
    username="hellowaoeu",
    password="badpassword\\",
    email="email@realemail.com"
)
INVALID_USER8 = User(
    username="hellowaoeu",
    password="badpassword\\",
    email="emailrealemail.com"
)
INVALID_USER9 = User(
    username="hellowaoeu",
    password="badpassword\\",
    email="ema @aoeu.com"
)
INVALID_USER10 = User(
    username="hellowao((((eu",
    password="password password",
    email="ema @aoeu.com"
)