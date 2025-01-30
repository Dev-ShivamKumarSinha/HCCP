from django.db import connection

# Fetch the latest version of an article efficiently.
def get_latest_article_version(article_id):
    query = """
    SELECT v.id, v.body, v.updated_at, u.username AS updated_by
    FROM articles_articleversion v
    JOIN auth_user u ON v.updated_by_id = u.id
    WHERE v.article_id = %s
    ORDER BY v.version_number DESC
    LIMIT 1
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [article_id])
        row = cursor.fetchone()

    if row:
        return {
            "version_id": row[0],
            "body": row[1],
            "updated_at": row[2],
            "updated_by": row[3],
        }
    return None

# Fetch article version history efficiently.
def get_article_history(article_id):
    query = """
    SELECT v.version_number, v.body, v.updated_at, u.username AS updated_by
    FROM articles_articleversion v
    JOIN auth_user u ON v.updated_by_id = u.id
    WHERE v.article_id = %s
    ORDER BY v.version_number DESC
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [article_id])
        results = cursor.fetchall()

    return [
        {
            "version": row[0],
            "body": row[1],
            "updated_at": row[2],
            "updated_by": row[3]
        }
        for row in results
    ]

# Fetch all user activity logs (edits, deletes, rollbacks).
def get_user_activity_logs():
    query = """
    SELECT l.id, u.username, l.action, a.title AS article_title, l.timestamp
    FROM articles_useractivitylog l
    JOIN auth_user u ON l.user_id = u.id
    LEFT JOIN articles_article a ON l.article_id = a.id
    ORDER BY l.timestamp DESC
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()

    return [
        {
            "id": row[0],
            "username": row[1],
            "action": row[2],
            "article_title": row[3],
            "timestamp": row[4],
        }
        for row in results
    ]

# Aggregate total edits by user.
def get_user_edit_counts():
    query = """
    SELECT u.username, COUNT(l.id) AS edit_count
    FROM articles_useractivitylog l
    JOIN auth_user u ON l.user_id = u.id
    WHERE l.action = 'edit'
    GROUP BY u.username
    ORDER BY edit_count DESC
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()

    return [{"username": row[0], "edit_count": row[1]} for row in results]
