import mysql.connector

def get_all_universities():
    cnx = mysql.connector.connect(
        user='root',
        password='root',
        host='localhost',
        database='academicworld'
    )
    cursor = cnx.cursor()
    cursor.execute("SELECT DISTINCT name FROM university ORDER BY name;")
    results = [row[0] for row in cursor.fetchall()]
    cursor.close()
    cnx.close()
    return results


def get_faculty_by_keywords(keyword):
    cnx = mysql.connector.connect(
        user='root',
        password='root',
        host='localhost',
        database='academicworld'
    )
    cursor = cnx.cursor()

    # placeholders = ','.join(['%s'] * len(keywords))

    base_query = f"""
        SELECT 
            f.name, f.position, f.photo_url,
            f.email,
            u.name, u.photo_url
        FROM faculty f
        JOIN faculty_keyword fk ON f.id = fk.faculty_id
        JOIN keyword k ON k.id = fk.keyword_id
        JOIN university u ON f.university_id = u.id
        WHERE k.name = %s
    """

    params = keyword

    #if university_filter:
     #   base_query += " AND u.name = %s"
      #  params.append(university_filter)

    base_query += """
        GROUP BY f.id
        LIMIT 10;
    """

    cursor.execute(base_query, (keyword,))
    results = cursor.fetchall()
    cursor.close()
    cnx.close()
    return results


def get_all_keywords():
    cnx = mysql.connector.connect(
        user='root',
        password='root',
        host='localhost',
        database='academicworld'
    )
    cursor = cnx.cursor()
    cursor.execute("SELECT DISTINCT name FROM keyword ORDER BY name")
    keywords = [row[0] for row in cursor.fetchall()]
    cursor.close()
    cnx.close()
    return keywords
