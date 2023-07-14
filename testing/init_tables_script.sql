use database1;

drop table actions;
drop table plans;
drop table todos_in_day;
drop table todos;
drop table alerts;
drop table events_in_day;
drop table events;
drop table goals;
drop table desires;
drop table recurrences;
drop table months_accessed_by_user;
drop table users;


create table users (
user_id int unsigned not null primary key auto_increment,
username varchar(24) not null,
hashed_password tinyblob not null,
date_joined bigint not null,
salt tinyblob not null,
email varchar(32),
google_calendar_id varchar(84));

CREATE UNIQUE INDEX username_index ON users(username);

create table months_accessed_by_user(
month int not null,
year int not null,
user_id int unsigned not null,

FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
PRIMARY KEY (month, year, user_id)
);

CREATE INDEX user_id_index ON months_accessed_by_user(user_id);

create table recurrences (
recurrence_id bigint unsigned not null primary key auto_increment,
user_id int unsigned not null,
rrule_string varchar(64) not null,
start_instant bigint not null,

-- recurrent event stuff
event_name varchar(64),
event_type int not null,
event_description varchar(500),
event_duration int not null,

-- recurrent todo stuff
todo_name varchar(32),
todo_timeframe int, -- can be a day, a week, or a month in length, depending on rrule

-- recurrent goal stuff
goal_name varchar(42) not null,
goal_how_much int,
goal_measuring_units varchar(12),
goal_timeframe int not null, -- can be a day, a week, or a month in length, depending on rrule
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE);
CREATE INDEX user_id_index ON recurrences(user_id);

create table desires(
desire_id int unsigned not null primary key auto_increment,
name varchar(42) not null,
user_id int unsigned not null,
deadline bigint,
priority_level int,
color_r tinyint unsigned not null,
color_g tinyint unsigned not null,
color_b tinyint unsigned not null,
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE);

CREATE INDEX user_id_index ON desires(user_id);

create table goals(
goal_id bigint unsigned primary key not null auto_increment,
desire_id int unsigned not null,
user_id int unsigned not null,
name varchar(42) not null,
how_much int,
measuring_units varchar(12),
start_instant bigint not null,
end_instant bigint, -- null == goal is indefinite. This parameter is overridden by timeframe in recurring goals
-- recurring goal stuff
recurrence_id bigint unsigned,
timeframe int, -- can be a day, a week, or a month in length, depending on rrule


FOREIGN KEY (recurrence_id) REFERENCES recurrences(recurrence_id),
FOREIGN KEY (desire_id)REFERENCES desires(desire_id),
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE);

CREATE INDEX desire_id_index ON goals(desire_id);

create table events(
event_id bigint unsigned primary key auto_increment not null,
user_id int unsigned not null,
name varchar(64),
description varchar(500),
event_type int not null,
start_instant bigint not null,
end_instant bigint not null,
duration int not null,
-- start_day int unsigned not null,
-- end_day int unsigned not null,

linked_goal_id bigint unsigned,
recurrence_id bigint unsigned,

FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
FOREIGN KEY (linked_goal_id) REFERENCES goals(goal_id),
FOREIGN KEY (recurrence_id) REFERENCES recurrences(recurrence_id),
FOREIGN KEY (alert_id) REFERENCES alerts(alert_id));

create table events_in_day(
day bigint not null,
event_id bigint unsigned not null,
user_id int unsigned not null,

FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
FOREIGN KEY (event_id) REFERENCES events(event_id),
PRIMARY KEY (day, event_id));

CREATE INDEX day_user_index ON events_in_day (day, user_id);

create table alerts(
event_id bigint unsigned not null,
when int unsigned not null, -- when the alert should sound

FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
PRIMARY KEY (event_id, when));

create table todos(
todo_id bigint unsigned primary key not null auto_increment,
user_id int unsigned not null,

name varchar(32),
timeframe int not null, -- todos can either span a day, week, or month. timeframe specifies this
start_instant bigint not null,

recurrence_id bigint unsigned,
linked_goal_id bigint unsigned,

FOREIGN KEY (linked_goal_id) REFERENCES goals(goal_id),
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
FOREIGN KEY (recurrence_id) REFERENCES recurrences(recurrence_id));

create table todos_in_day(
day bigint not null,
todo_id bigint unsigned not null,
user_id int unsigned not null,

FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
FOREIGN KEY (todo_id) REFERENCES todos(todo_id),
PRIMARY KEY (day, todo_id));

CREATE INDEX day_user_index ON todos_in_day (day, user_id);

create table plans(
plan_id bigint unsigned primary key not null auto_increment,
user_id int unsigned not null,
goal_id bigint unsigned not null,
event_id bigint unsigned not null,
how_much int,
-- plan_description varchar(500), # same as the event description

FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
FOREIGN KEY (goal_id) REFERENCES goals(goal_id) ON DELETE CASCADE,
FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE);

CREATE INDEX goal_id_index ON plans(goal_id);
CREATE INDEX event_id_index ON plans(event_id);

create table actions(
plan_id bigint unsigned primary key not null,
event_id bigint unsigned not null,
goal_id bigint unsigned not null,
user_id int unsigned not null,
successful int,
how_much_accomplished int,
notes varchar(1000),

FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
FOREIGN KEY (plan_id) REFERENCES plans (plan_id) ON DELETE CASCADE,
FOREIGN KEY (goal_id) REFERENCES goals(goal_id) ON DELETE CASCADE,
FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE);

CREATE INDEX user_id_index ON actions(user_id);
CREATE INDEX event_id_index ON actions(event_id);
