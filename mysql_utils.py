import mysql.connector

def get_all_universities():
    cnx = mysql.connector.connect(
        user='root',
        password='Apb_0328',
        host='localhost',
        database='academicworld'
    )
    cursor = cnx.cursor()
    cursor.execute("SELECT DISTINCT name FROM university ORDER BY name;")
    results = [row[0] for row in cursor.fetchall()]
    cursor.close()
    cnx.close()
    return results


def get_faculty_by_keywords(keywords):
    cnx = mysql.connector.connect(
        user='root',
        password='Apb_0328',
        host='localhost',
        database='academicworld'
    )
    cursor = cnx.cursor()

    placeholders = ','.join(['%s'] * len(keywords))

    base_query = f"""
        SELECT 
            f.name, f.position, f.photo_url,
            f.email,
            u.name, u.photo_url
        FROM faculty f
        JOIN faculty_keyword fk ON f.id = fk.faculty_id
        JOIN keyword k ON k.id = fk.keyword_id
        JOIN university u ON f.university_id = u.id
        WHERE k.name IN ({placeholders})
    """

    params = keywords


    base_query += """
        GROUP BY f.id
        LIMIT 10;
    """

    cursor.execute(base_query, params)
    results = cursor.fetchall()
    cursor.close()
    cnx.close()
    return results


def get_all_keywords():
    cnx = mysql.connector.connect(
        user='root',
        password='Apb_0328',
        host='localhost',
        database='academicworld'
    )
    cursor = cnx.cursor()
    cursor.execute("SELECT DISTINCT name FROM keyword ORDER BY name")
    keywords = [row[0] for row in cursor.fetchall()]
    cursor.close()
    cnx.close()
    return keywords


def get_university_pub_counts_by_keyword(keyword, top_n=10):
    cnx = mysql.connector.connect(
        user="root",
        password="Apb_0328",
        host="localhost",
        database="academicworld",
    )
    cur = cnx.cursor()

    sql = """
    SELECT u.name AS university, COUNT(DISTINCT p.ID) AS total
    FROM publication p
    JOIN Publication_Keyword pk ON pk.publication_id = p.ID
    JOIN keyword k ON k.id = pk.keyword_id
    JOIN faculty_publication fp ON fp.publication_id = p.ID
    JOIN faculty f ON f.id = fp.faculty_id
    JOIN university u ON u.id = f.university_id
    WHERE LOWER(k.name) = LOWER(%s)           -- exact, case-insensitive match
    GROUP BY u.id, u.name
    ORDER BY total DESC
    LIMIT %s;
    """

    cur.execute(sql, (keyword, top_n))
    rows = cur.fetchall()
    cur.close()
    cnx.close()
    return rows
