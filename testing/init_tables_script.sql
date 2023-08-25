use u679652356_rm_lp_db_test;

drop table alerts;
drop table months_accessed_by_user;
drop table todos_without_deadline;
drop table goals_without_deadline;
drop table events_in_day;
drop table todos_in_day;
drop table goals_in_day;
drop table plans;
drop table events;
drop table todos;
drop table goals;
drop table recurrences;
drop table desires;
drop table users;


create table users (
    user_id int unsigned primary key auto_increment,
    username varchar(24) not null,
    hashed_password tinyblob not null,
    salt tinyblob not null,
    date_joined double not null,
    email varchar(42),
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
    date_created double not null,
    deadline double,
    date_retired double,
    priority_level int,
    color_r float unsigned not null,
    color_g float unsigned not null,
    color_b float unsigned not null,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX user_id_index ON desires(user_id);

create table recurrences (
    recurrence_id bigint unsigned not null primary key auto_increment,
    user_id int unsigned not null,
    rrule_string varchar(64) not null,
    start_instant double not null,

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
    how_much float not null,
    measuring_units varchar(12),
    start_instant double not null,
    end_instant double, -- null == goal is indefinite.
    -- recurring goal stuff
    recurrence_id bigint unsigned,
    recurrence_day double,

    FOREIGN KEY (recurrence_id) REFERENCES recurrences(recurrence_id),
    FOREIGN KEY (desire_id) REFERENCES desires(desire_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX desire_id_index ON goals(desire_id);
CREATE INDEX recurrence_id_and_day_index ON goals(recurrence_id, recurrence_day);

create table goals_without_deadline(
    goal_id BIGINT UNSIGNED NOT NULL,
    user_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (goal_id),
    FOREIGN KEY (goal_id) REFERENCES goals(goal_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX user_id_index ON users(user_id);

create table goals_in_day(
    day double not null,
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
    start_instant double not null,
    deadline double,

    recurrence_id bigint unsigned,
    recurrence_day double,
    linked_goal_id bigint unsigned,

    FOREIGN KEY (linked_goal_id) REFERENCES goals(goal_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (recurrence_id) REFERENCES recurrences(recurrence_id)
);
CREATE INDEX recurrence_id_and_day_index ON todos(recurrence_id, recurrence_day);

CREATE TABLE todos_without_deadline(
    todo_id bigint unsigned not null,
    user_id int unsigned not null,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (todo_id) REFERENCES todos(todo_id),
    PRIMARY KEY (todo_id)
);
CREATE INDEX user_index ON todos_without_deadline (user_id);

create table todos_in_day(
    day double not null,
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
    is_hidden bit not null,
    start_instant double not null,
    end_instant double not null,

    linked_goal_id bigint unsigned,
    linked_todo_id bigint unsigned,
    recurrence_id bigint unsigned,
    recurrence_day double,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (linked_goal_id) REFERENCES goals(goal_id),
    FOREIGN KEY (linked_todo_id) REFERENCES todos(todo_id),
    FOREIGN KEY (recurrence_id) REFERENCES recurrences(recurrence_id)
);
CREATE INDEX todo_id_index ON events (linked_todo_id);
CREATE INDEX recurrence_id_and_day_index ON events(recurrence_id, recurrence_day);

create table events_in_day(
    day double not null,
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
    goal_id bigint unsigned not null,
    event_id bigint unsigned not null,
    how_much float not null,
    how_much_accomplished float,
    notes varchar(300),

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (goal_id) REFERENCES goals(goal_id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
);
CREATE INDEX goal_id_index ON plans(goal_id);
CREATE INDEX event_id_index ON plans(event_id);