from backend.database import get_connection


# ==========================================
# STUDENT EXPENSE SUMMARY
# ==========================================

def get_student_summary():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            s.student_id,
            s.name,
            s.monthly_budget,
            COALESCE(SUM(e.amount), 0) AS total_expense,
            s.monthly_budget - COALESCE(SUM(e.amount), 0)
                AS remaining_budget
        FROM students s
        LEFT JOIN expenses e
            ON s.student_id = e.student_id
        GROUP BY
            s.student_id,
            s.name,
            s.monthly_budget
        ORDER BY total_expense DESC
    """

    cursor.execute(query)

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    return result


# ==========================================
# CATEGORY EXPENSE SUMMARY
# ==========================================

def get_category_summary():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            category,
            SUM(amount) AS total_expense
        FROM expenses
        GROUP BY category
        ORDER BY total_expense DESC
    """

    cursor.execute(query)

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    return result


# ==========================================
# DAILY EXPENSE SUMMARY
# ==========================================

def get_daily_expense_summary():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            expense_date,
            SUM(amount) AS total_expense
        FROM expenses
        GROUP BY expense_date
        ORDER BY expense_date
    """

    cursor.execute(query)

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    return result


# ==========================================
# BUDGET UTILIZATION
# ==========================================

def get_budget_utilization():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            s.student_id,
            s.name,
            s.monthly_budget,
            COALESCE(SUM(e.amount), 0) AS total_expense,

            ROUND(
                (
                    COALESCE(SUM(e.amount), 0)
                    / NULLIF(s.monthly_budget, 0)
                ) * 100,
                2
            ) AS utilization_percentage

        FROM students s

        LEFT JOIN expenses e
            ON s.student_id = e.student_id

        GROUP BY
            s.student_id,
            s.name,
            s.monthly_budget

        ORDER BY utilization_percentage DESC
    """

    cursor.execute(query)

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    return result