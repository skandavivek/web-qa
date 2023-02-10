import os
import psycopg2

conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user='postgres',
        password='1234')

# Open a cursor to perform database operations
cur = conn.cursor()

# Execute a command: this creates a new table
cur.execute('DROP TABLE IF EXISTS qa2;')
cur.execute('CREATE TABLE qa2 (id serial PRIMARY KEY,'
                                 'URL text,'
                                 'question text,'
                                 'answer text,'
                                 'created_at TIMESTAMP DEFAULT NOW());'
                                 )

# Insert data into the table

# cur.execute('INSERT INTO books (title, author, pages_num, review)'
#             'VALUES (%s, %s, %s, %s)',
#             ('A Tale of Two Cities',
#              'Charles Dickens',
#              489,
#              'A great classic!')
#             )


# cur.execute('INSERT INTO books (title, author, pages_num, review)'
#             'VALUES (%s, %s, %s, %s)',
#             ('Anna Karenina',
#              'Leo Tolstoy',
#              864,
#              'Another great classic!')
#             )

conn.commit()

cur.close()
conn.close()