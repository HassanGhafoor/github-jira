import sqlite3

conn = sqlite3.connect("app/dev.sqlite")
cursor = conn.cursor()

print("Ticket Logs:")
for row in cursor.execute("SELECT * FROM ticket_logs;"):
    print(row)

conn.close()
