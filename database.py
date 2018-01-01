from KotoBlockchainParser import Block
import mysql.connector

with open("config.json", "r") as f:
	o = json.load(f)
for k in o:
	globals()[k] = o[k]

sql = mysql.connector.connect(
    host = DB_HOST,
    port = DB_PORT
    user = DB_USER,
    password = DB_PASSWORD,
    database = DB_NAME
)
