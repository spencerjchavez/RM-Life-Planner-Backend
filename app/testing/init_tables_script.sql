DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS months_accessed_by_user;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS todos;
DROP TABLE IF EXISTS goals;
DROP TABLE IF EXISTS recurrences;
DROP TABLE IF EXISTS desires;
DROP TABLE IF EXISTS user_preferences;
DROP TABLE IF EXISTS users;



create table users (
    user_id int unsigned primary key auto_increment,
    username varchar(24) not null,
    hashed_password tinyblob not null,
    date_joined DATE not null,
    email varchar(42),
    google_calendar_id varchar(84)
);
CREATE UNIQUE INDEX username_index ON users(username);

CREATE TABLE user_preferences (
    user_id INT UNSIGNED PRIMARY KEY,

    highest_priority_color varchar(8) not null,
    very_high_priority_color varchar(8) not null,
    high_priority_color varchar(8) not null,
    medium_priority_color varchar(8) not null,
    low_priority_color varchar(8) not null,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

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
    date_created DATE not null,
    deadline DATE,
    date_retired DATE,
    priority_level int,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX user_id_index ON desires(user_id);

create table recurrences (
    recurrence_id bigint unsigned not null primary key auto_increment,
    user_id int unsigned not null,
    rrule_string varchar(64) not null,
    start_date DATE not null,
    start_time TIME not null,

    -- recurrent event stuff
    event_name varchar(64),
    event_description varchar(500),
    event_duration double,

    -- recurrent doto stuff
    todo_name varchar(32),
    todo_timeframe ENUM ('DAY', 'WEEK', 'MONTH', 'YEAR'), -- can be a day, a week, or a month in length, depending on rrule
    todo_how_much_planned float,

    -- recurrent goal stuff
    goal_name varchar(42),
    goal_desire_id bigint unsigned,
    goal_how_much float,
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
    start_date DATE not null,
    deadline_date DATE, -- null == goal is indefinite.
    -- recurring goal stuff
    recurrence_id bigint unsigned,
    recurrence_date DATE,

    FOREIGN KEY (recurrence_id) REFERENCES recurrences(recurrence_id),
    FOREIGN KEY (desire_id) REFERENCES desires(desire_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX desire_id_index ON goals(desire_id);
CREATE INDEX recurrence_id_and_date_index ON goals(recurrence_id, recurrence_date);
CREATE INDEX user_id_index ON goals(user_id);
CREATE INDEX start_date_index ON goals(start_date);
CREATE INDEX deadline_date_index ON goals(deadline_date);

create table todos(
    todo_id bigint unsigned primary key not null auto_increment,
    user_id int unsigned not null,

    name varchar(32),
    start_date DATE NOT NULL,
    deadline_date DATE,
    how_much_planned FLOAT NOT NULL,

    recurrence_id bigint unsigned,
    recurrence_date DATE,
    linked_goal_id bigint unsigned,

    FOREIGN KEY (linked_goal_id) REFERENCES goals(goal_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (recurrence_id) REFERENCES recurrences(recurrence_id)
);
CREATE INDEX recurrence_id_and_date_index ON todos(recurrence_id, recurrence_date);
CREATE INDEX user_id_index ON todos(user_id);
CREATE INDEX start_date_index ON todos(start_date);
CREATE INDEX deadline_date_index ON todos(deadline_date);

create table events(
    event_id bigint unsigned primary key auto_increment not null,
    user_id int unsigned not null,
    name varchar(64),
    description varchar(500),
    is_hidden bit not null,
    start_date DATE not null,
    start_time TIME not null,
    end_date DATE not null,
    end_time TIME not null,

    linked_todo_id bigint unsigned,
    linked_goal_id BIGINT UNSIGNED,

    how_much_accomplished float,
    notes varchar(300),

    recurrence_id bigint unsigned,
    recurrence_date DATE,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (linked_todo_id) REFERENCES todos(todo_id),
    FOREIGN KEY (recurrence_id) REFERENCES recurrences(recurrence_id)
);
CREATE INDEX todo_id_index ON events (linked_todo_id);
CREATE INDEX goal_id_index ON events (linked_goal_id);
CREATE INDEX recurrence_id_and_date_index ON events(recurrence_id, recurrence_date);
CREATE INDEX start_date_index ON events(start_date);
CREATE INDEX end_date_index ON events(end_date);


create table alerts(
    event_id bigint unsigned not null,
    user_id bigint unsigned not null,
    time TIME not null, -- when the alert should sound

    FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, time)
);