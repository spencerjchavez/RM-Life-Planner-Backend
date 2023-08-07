use database1;

drop table actions;
drop table plans;
drop table alerts;
drop table events_in_day;
drop table events;
drop table todos_in_day;
drop table todos_without_deadline;
drop table todos;
drop table goals_in_day;
drop table goals_without_deadline;
drop table goals;
drop table recurrences;
drop table desires;
drop table months_accessed_by_user;
drop table users;


create table users (
    user_id int unsigned primary key auto_increment,
    username varchar(24) not null,
    hashed_password tinyblob not null,
    salt tinyblob not null,
    date_joined bigint not null,
    email varchar(32),
    google_calendar_id varchar(84)
);
CREATE UNIQUE INDEX username_index ON users(username);

create table months_accessed_by_user(
    user_id int unsigned not null,
    year int not null,
    month int not null,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    PRIMARY KEY (month, year, user_id)
);
CREATE INDEX user_id_index ON months_accessed_by_user(user_id);

create table desires(
    desire_id bigint unsigned not null primary key auto_increment,
    name varchar(42) not null,
    user_id int unsigned not null,
    date_created bigint not null,
    deadline bigint,
    date_retired bigint,
    priority_level int,
    color_r tinyint unsigned not null,
    color_g tinyint unsigned not null,
    color_b tinyint unsigned not null,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX user_id_index ON desires(user_id);

create table recurrences (
    recurrence_id bigint unsigned not null primary key auto_increment,
    user_id int unsigned not null,
    rrule_string varchar(64) not null,
    start_instant bigint not null,

    -- recurrent event stuff
    event_name varchar(64),
    event_description varchar(500),
    event_duration int not null,

    -- recurrent todo stuff
    todo_name varchar(32),
    todo_timeframe ENUM ('DAY', 'WEEK', 'MONTH', 'YEAR'), -- can be a day, a week, or a month in length, depending on rrule

    -- recurrent goal stuff
    goal_name varchar(42),
    goal_desire_id bigint unsigned,
    goal_how_much int,
    goal_measuring_units varchar(12),
    goal_timeframe ENUM ('DAY', 'WEEK', 'MONTH', 'YEAR'), -- can be a day, a week, or a month in length, depending on rrule
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (goal_desire_id) REFERENCES desires(desire_id)
);
CREATE INDEX user_id_index ON recurrences(user_id);

create table goals(
    goal_id bigint unsigned primary key not null auto_increment,
    desire_id bigint unsigned not null,
    user_id int unsigned not null,
    name varchar(42) not null,
    how_much float,
    measuring_units varchar(12),
    start_instant bigint not null,
    deadline bigint, -- null == goal is indefinite.
    -- recurring goal stuff
    recurrence_id bigint unsigned,
    recurrence_day bigint,

    FOREIGN KEY (recurrence_id) REFERENCES recurrences(recurrence_id),
    FOREIGN KEY (desire_id)REFERENCES desires(desire_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX desire_id_index ON goals(desire_id);
CREATE INDEX recurrence_id_and_day_index ON goals(recurrence_id, recurrence_day);

create table goals_without_deadline(
    goal_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    FOREIGN KEY (goal_id) REFERENCES goals(goal_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    PRIMARY KEY (goal_id)
);
CREATE INDEX user_id_index ON users(user_id) ON DELETE CASCADE;

create table goals_in_day(
    day bigint not null,
    goal_id bigint unsigned not null,
    user_id int unsigned not null,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (goal_id) REFERENCES goals(goal_id),
    PRIMARY KEY (day, goal_id)
);
CREATE INDEX day_user_index ON goals_in_day (day, user_id);

create table todos(
    todo_id bigint unsigned primary key not null auto_increment,
    user_id int unsigned not null,

    name varchar(32),
    start_instant bigint not null,
    deadline bigint,

    recurrence_id bigint unsigned,
    recurrence_day bigint,
    linked_goal_id bigint unsigned,

    FOREIGN KEY (linked_goal_id) REFERENCES goals(goal_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (recurrence_id) REFERENCES recurrences(recurrence_id)
);
CREATE INDEX recurrence_id_and_day_index ON todos(recurrence_id, recurrence_day)

CREATE TABLE todos_without_deadline(
    todo_id bigint unsigned not null,
    user_id int unsigned not null,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (todo_id) REFERENCES todos(todo_id),
    PRIMARY KEY (todo_id)
);
CREATE INDEX user_index ON todos_without_deadline (user_id);

create table todos_in_day(
    day bigint not null,
    todo_id bigint unsigned not null,
    user_id int unsigned not null,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (todo_id) REFERENCES todos(todo_id),
    PRIMARY KEY (day, todo_id)
);
CREATE INDEX day_user_index ON todos_in_day (day, user_id);

create table events(
    event_id bigint unsigned primary key auto_increment not null,
    user_id int unsigned not null,
    name varchar(64),
    description varchar(500),
    is_hidden bool not null,
    start_instant bigint not null,
    end_instant bigint not null,
    duration int not null,

    linked_goal_id bigint unsigned,
    linked_todo_id bigint unsigned,
    recurrence_id bigint unsigned,
    recurrence_day bigint,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (linked_goal_id) REFERENCES goals(goal_id),
    FOREIGN KEY (linked_todo_id) REFERENCES todos(todo_id),
    FOREIGN KEY (recurrence_id) REFERENCES recurrences(recurrence_id)
);
CREATE INDEX todo_id_index ON events (linked_todo_id);
CREATE INDEX recurrence_id_and_day_index ON events(recurrence_id, recurrence_day)

create table events_in_day(
    day bigint not null,
    event_id bigint unsigned not null,
    user_id int unsigned not null,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    PRIMARY KEY (day, event_id)
);
CREATE INDEX day_user_index ON events_in_day (day, user_id);

create table alerts(
    event_id bigint unsigned not null,
    user_id bigint unsigned not null,
    time bigint not null, -- when the alert should sound

    FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, time)
);

create table plans(
    plan_id bigint unsigned primary key not null auto_increment,
    user_id int unsigned not null,
    goal_id bigint unsigned,
    event_id bigint unsigned not null,
    how_much float,
    -- plan_description varchar(500), # same as the event description

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (goal_id) REFERENCES goals(goal_id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
);
CREATE INDEX goal_id_index ON plans(goal_id);
CREATE INDEX event_id_index ON plans(event_id);

create table actions(
    plan_id bigint unsigned primary key not null,
    user_id int unsigned not null,
    successful int,
    how_much_accomplished float,
    notes varchar(1000),

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES plans (plan_id) ON DELETE CASCADE
);
CREATE INDEX user_id_index ON actions(user_id);
CREATE INDEX event_id_index ON actions(event_id);
