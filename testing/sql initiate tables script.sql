use users;
drop table user_ids;
create table user_ids (
username varchar(24) primary key not null,
user_id int unsigned not null);

drop table users;
create table users (
user_id int unsigned primary key not null auto_increment,
username varchar(24) not null,
hashed_password tinyblob not null,
date_joined bigint unsigned not null,
salt tinyblob not null,
email varchar(32),
google_calendar_id varchar(84));

use calendars;
drop table events_by_user_event_id;
create table events_by_user_event_id (
user_event_id bigint unsigned primary key not null,
start_time int unsigned not null,
end_time int unsigned not null,
duration int not null,
event_type int not null,
name varchar(64),
description varchar(500),
reminders varbinary(24),  # up to 3 reminders per event in epoch seconds

linked_goal_id int,
linked_plan_id int,
linked_action_id int,

rrule varchar(64),
event_recurrence_id bigint unsigned);

drop table events_by_user_day;
create table events_by_user_day (
key_id bigint unsigned primary key not null,
event_ids varbinary(444));

drop table recurrences;
create table recurrences (
recurrence_id bigint unsigned primary key not null,
user_id int unsigned not null,
recurrence_type int,
rrule_string varchar(64) not null,
recurrence_end_time bigint unsigned not null,
monthyears_buffered varbinary(1080), # represents 90 years worth of bufferings, from the first event onwards

# recurrent event stuff
event_type int not null,
event_name varchar(64),
event_description varchar(500),

#recurrent todo stuff
todo_name varchar(32),
todo_timeframe int);

drop table recurrence_ids_by_user;
create table recurrence_ids_by_user(
user_id int unsigned primary key not null,
recurrence_ids varbinary(8000));

use goal_achieving;

drop table desire_ids_by_user;
create table desire_ids_by_user(
user_id int unsigned primary key not null,
desire_ids varbinary(200));

drop table desires;
create table desires(
desire_id int unsigned primary key not null auto_increment,
name varchar(42) not null,
user_id int unsigned not null,
deadline_date bigint unsigned,
category_id int,
priority_level int,
color_r tinyint unsigned not null,
color_g tinyint unsigned not null,
color_b tinyint unsigned not null,
related_goal_ids varbinary(80));

drop table goal_ids_by_desire;
create table goal_ids_by_desire(
desire_id int unsigned primary key not null,
goal_ids varbinary(80)); # max 20 goals per desire

drop table goals;
create table goals(
goal_id int unsigned primary key not null auto_increment,
desire_id int unsigned not null,
user_id int unsigned not null,
name varchar(42) not null,
how_much int,
measuring_units varchar(12),

# if is recurring goal
rrule_string varchar(64),
recurrence_id bigint unsigned,
# if one-time goal
plan_id bigint unsigned);

drop table plans;
create table plans(
plan_id bigint unsigned primary key not null auto_increment,
user_id int unsigned not null,
goal_id int unsigned,
event_id int unsigned not null,
todo_id int unsigned,
plan_description varchar(500), # same as the event description
action_id bigint unsigned);

drop table actions;
create table actions(
action_id bigint unsigned primary key not null auto_increment,
event_id int unsigned not null,
plan_id bigint unsigned not null,
goal_id int unsigned not null,
successful int,
how_much_accompished int,
notes varchar(1000));

drop table todos_by_goal_day;
create table todos_by_goal_day(  # goal_id may be less than 4 bytes long, therefore always parse out the day first, and the goal second
key_id bigint unsigned primary key not null,
user_id int unsigned not null,
todo_event_ids varbinary(400));

drop table todos_by_goal_week;
create table todos_by_goal_week(
key_id bigint unsigned primary key not null,
user_id int unsigned not null,
todo_event_ids varbinary(400));

drop table todos_by_goal_month;
create table todos_by_goal_month(
key_id bigint unsigned primary key not null,
user_id int unsigned not null,
todo_ids varbinary(400));

drop table todos_by_user_event_id;
create table todos_by_user_event_id(
user_todo_id bigint unsigned primary key not null,
name varchar(32),
timeframe int,
recurrence_id bigint unsigned,

goal_id int unsigned,
plan_id bigint unsigned,
action_id bigint unsigned);
