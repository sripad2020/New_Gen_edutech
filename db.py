import sqlite3

connection=sqlite3.connect('users.db')
cursor=connection.cursor()

users="create table if not exists user_info(username varchar(200) NOT NULL, email varchar(200) NOT NULL, password varchar(200) NOT NULL,course VARCHAR(200) NOT NULL)"
cursor.execute(users)
