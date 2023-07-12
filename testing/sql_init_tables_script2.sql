use database;

drop table users;
create table users (
user_id int unsigned not null primary key auto_increment,
username varchar(24) not null,
hashed_password tinyblob not null,
date_joined int unsigned not null,
salt tinyblob not null,
email varchar(32),
google_calendar_id varchar(84),
events_owned int unsigned not null,
next_todo_id int unsigned not null);

CREATE UNIQUE INDEX username_index ON users(username);

drop table recurrences;
create table recurrences (
recurrence_id bigint unsigned not null auto_increment,
user_id int unsigned not null,
recurrence_type int,
rrule_string varchar(64) not null,
--recurrence_start_instant bigint not null,
--recurrence_end_instant bigint not null,
monthyears_buffered varbinary(1080), -- represents 90 years worth of bufferings, from the first event onwards. every byte represents 1 month

-- recurrent event stuff
event_type int not null,
event_name varchar(64),
event_description varchar(500),
event_duration int not null,

-- recurrent todo stuff
todo_name varchar(32),
todo_timeframe int, -- can be a day, a week, or a month in length, depending on rrule

--recurrent goal stuff
goal_name varchar(42) not null,
goal_how_much int,
goal_measuring_units varchar(12),
goal_timeframe int not null, -- can be a day, a week, or a month in length, depending on rrule

FOREIGN KEY user_id REFERENCES users(user_id),
PRIMARY KEY recurrence_id);

CREATE INDEX user_id_index ON recurrences(user_id);

drop table desires;
create table desires(
desire_id int unsigned not null auto_increment,
name varchar(42) not null,
user_id int unsigned not null,
deadline_date bigint unsigned,
priority_level int,
color_r tinyint unsigned not null,
color_g tinyint unsigned not null,
color_b tinyint unsigned not null,

FOREIGN KEY user_id REFERENCES users(user_id));

CREATE INDEX user_id_index ON desires(user_id);

drop table goals;
create table goals(
goal_id bigint unsigned primary key not null auto_increment,
desire_id int unsigned not null,
user_id int unsigned not null,
name varchar(42) not null,
how_much int,
measuring_units varchar(12),
start_instant int unsigned not null,
end_instant int unsigned, -- null == goal is indefinite. This parameter is overridden by timeframe in recurring goals
-- recurring goal stuff
recurrence_id bigint unsigned,
timeframe int, -- can be a day, a week, or a month in length, depending on rrule


FOREIGN KEY recurrence_id REFERENCES recurrences(recurrence_id),
FOREIGN desire_id REFERENCES desires(desire_id),
FOREIGN KEY user_id REFERENCES users(user_id),
);
CREATE INDEX desire_id_index ON goals(desire_id)

drop table events;
create table events(
event_id bigint unsigned primary key auto_increment not null,
user_id int unsigned not null,
name varchar(64),
description varchar(500),
event_type int not null,
start_instant int unsigned not null,
end_instant int unsigned not null,
duration int not null,
--start_day int unsigned not null,
--end_day int unsigned not null,

reminders varbinary(24),  -- up to 3 reminders per event in epoch seconds

linked_goal_id int,
recurrence_id bigint unsigned,

FOREIGN KEY user_id REFERENCES users(user_id),
FOREIGN KEY linked_goal_id REFERENCES goals(goal_id),
FOREIGN KEY recurrence_id REFERENCES recurrences(recurrence_id));

drop table events_in_day;
create table events_in_day(
day int unsigned not null,
event_id bigint unsigned not null,
user_id int unsigned not null,

FOREIGN KEY user_id REFERENCES users(user_id),
FOREIGN KEY event_id REFERENCES events(event_id),
PRIMARY KEY (day, event_id));

CREATE INDEX day_user_index ON events_in_day (day, user_id);

drop table todos
create table todos(
todo_id bigint unsigned primary key not null auto_increment,
user_id int unsigned not null,

name varchar(32),
timeframe int not null, -- todos can either span a day, week, or month. timeframe specifies this
start_instant int unsigned not null,

recurrence_id bigint unsigned,
linked_goal_id bigint unsigned,

FOREIGN KEY linked_goal_id REFERENCES goals(goal_id),
FOREIGN KEY user_id REFERENCES users(user_id),
FOREIGN KEY recurrence_id REFERENCES recurrences(recurrence_id));

drop table todos_in_day;
create table todos_in_day(
day int unsigned not null,
todo_id bigint unsigned not null,
user_id int unsigned not null,

FOREIGN KEY user_id REFERENCES users(user_id),
FOREIGN KEY todo_id REFERENCES todos(todo_id),
PRIMARY KEY (day, todo_id));

CREATE INDEX day_user_index ON todos_in_day (day, user_id);

drop table plans;
create table plans(
plan_id bigint unsigned primary key not null auto_increment,
user_id int unsigned not null,
goal_id int unsigned not null,
event_id int unsigned not null,
how_much int,
-- plan_description varchar(500), # same as the event description

FOREIGN KEY user_id REFERENCES users(user_id),
FOREIGN KEY goal_id REFERENCES goals(goal_id),
FOREIGN KEY event_id REFERENCES events(event_id));

CREATE INDEX goal_id_index ON plans(goal_id);
CREATE INDEX event_id_index ON plans(event_id);

drop table actions;
create table actions(
plan_id bigint unsigned primary key not null,
event_id int unsigned not null,
goal_id int unsigned not null,
user_id int unsigned not null,
successful int,
how_much_accomplished int,
notes varchar(1000),

FOREIGN KEY user_id REFERENCES users(user_id),
FOREIGN KEY plan_id REFERENCES plans (plan_id),
FOREIGN KEY goal_id REFERENCES goals(goal_id),
FOREIGN KEY event_id REFERENCES events(event_id));

CREATE INDEX user_id_index ON actions(user_id);
CREATE INDEX event_id_index ON actions(event_id);
