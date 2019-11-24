#######################
## Private Functions ##
#######################

# Importing mysql connector
import mysql.connector

user = 'root'
password = 'dermdermderm99'
host = 'localhost'

# Function that builds the mysql connector for us, using our information stored here
def init_mysql(database):
    # print("Building a MySQL connector")
    connector = mysql.connector.connect(user=user, password=password, host=host, database=database)
    return connector

def build_edit_query(dataset, table):
    query = "UPDATE " + str(table) + " "

    for entry in dataset:
        query = query + " SET " + entry + " = %s, "

    query = query[0:len(query)-2]

    return query