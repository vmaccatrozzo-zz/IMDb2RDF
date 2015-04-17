import MySQLdb

db = MySQLdb.connect("127.0.0.1","root","","imdb2")
cursor = db.cursor()

cursor.execute("SELECT person_id, info_type_id, info FROM person_info WHERE person_id=%s",('4089689'))
data = cursor.fetchall()
type = info_type[row[1]]
info = row[2]
if type =='spouse':
	print info 
