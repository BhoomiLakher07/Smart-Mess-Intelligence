
import pandas as pd
from io import BytesIO

from backend.database import get_connection


# ==========================================
# EXPORT EXPENSES TO EXCEL
# ==========================================

def export_expenses_to_excel():
    connection = get_connection()

    try:
        query = """
            SELECT
                e.expense_id,
                e.student_id,
                s.name AS student_name,
                e.expense_date,
                e.category,
                e.item,
                e.amount,
                e.description
            FROM expenses e
            JOIN students s
                ON e.student_id = s.student_id
            ORDER BY e.expense_date, e.expense_id
        """

        dataframe = pd.read_sql(query, connection)

    finally:
        connection.close()

    excel_file = BytesIO()

    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        dataframe.to_excel(
            writer,
            index=False,
            sheet_name="Expenses"
        )

    excel_file.seek(0)
    return excel_file


# ==========================================
# IMPORT EXPENSES FROM EXCEL
# ==========================================

def import_expenses_from_excel(file):

    if isinstance(file, bytes):
        file = BytesIO(file)

    dataframe = pd.read_excel(file)

    # Required columns in the uploaded Excel file
    required_columns = [
        "student_id",
        "category",
        "amount",
        "expense_date"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    dataframe = dataframe.dropna(how="all").copy()

    if dataframe.empty:
        raise ValueError("The Excel file contains no expense records.")

    # Item is optional in Excel; use category as its fallback.
    if "item" not in dataframe.columns:
        dataframe["item"] = dataframe["category"]
    else:
        dataframe["item"] = dataframe["item"].where(
            dataframe["item"].notna(),
            dataframe["category"]
        )

    # Description is optional.
    if "description" not in dataframe.columns:
        dataframe["description"] = None

    # Validate student IDs
    if dataframe["student_id"].isnull().any():
        raise ValueError("Student ID cannot be empty.")

    numeric_ids = pd.to_numeric(
        dataframe["student_id"],
        errors="coerce"
    )

    if (
        numeric_ids.isnull().any()
        or (numeric_ids % 1 != 0).any()
        or (numeric_ids <= 0).any()
    ):
        raise ValueError("Student IDs must be positive whole numbers.")

    dataframe["student_id"] = numeric_ids.astype(int)

    # Validate category and item
    for column in ["category", "item"]:
        if dataframe[column].isnull().any():
            raise ValueError(f"{column.capitalize()} cannot be empty.")

        dataframe[column] = (
            dataframe[column].astype(str).str.strip()
        )

        if (
            dataframe[column].eq("").any()
            or dataframe[column].str.lower().eq("nan").any()
        ):
            raise ValueError(f"{column.capitalize()} cannot be empty.")

    if dataframe["category"].str.len().gt(50).any():
        raise ValueError("Category must not exceed 50 characters.")

    if dataframe["item"].str.len().gt(100).any():
        raise ValueError("Item must not exceed 100 characters.")

    # Validate amount
    dataframe["amount"] = pd.to_numeric(
        dataframe["amount"],
        errors="coerce"
    )

    if dataframe["amount"].isnull().any():
        raise ValueError("Amount must contain valid numbers.")

    if (
        (~dataframe["amount"].map(
            lambda value: pd.notna(value)
            and abs(value) != float("inf")
        )).any()
        or (dataframe["amount"] <= 0).any()
    ):
        raise ValueError("Amount must be a finite number greater than 0.")

    # Validate dates
    dataframe["expense_date"] = pd.to_datetime(
        dataframe["expense_date"],
        errors="coerce"
    )

    if dataframe["expense_date"].isnull().any():
        raise ValueError("Expense date contains invalid dates.")

    dataframe["expense_date"] = dataframe["expense_date"].dt.date

    # Clean optional descriptions
    dataframe["description"] = dataframe["description"].where(
        dataframe["description"].notna(),
        None
    )

    dataframe["description"] = dataframe["description"].map(
        lambda value: (
            str(value).strip()[:255]
            if value is not None and str(value).strip()
            else None
        )
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Confirm every student exists before inserting anything.
        student_ids = tuple(dataframe["student_id"].unique().tolist())
        placeholders = ", ".join(["%s"] * len(student_ids))

        cursor.execute(
            f"""
                SELECT student_id
                FROM students
                WHERE student_id IN ({placeholders})
            """,
            student_ids
        )

        valid_student_ids = {
            row[0] for row in cursor.fetchall()
        }

        invalid_student_ids = sorted(
            set(student_ids) - valid_student_ids
        )

        if invalid_student_ids:
            raise ValueError(
                "Invalid student ID(s): "
                + ", ".join(map(str, invalid_student_ids))
            )

        insert_query = """
            INSERT INTO expenses (
                student_id,
                expense_date,
                category,
                item,
                amount,
                description
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        records = [
            (
                int(row.student_id),
                row.expense_date,
                row.category,
                row.item,
                float(row.amount),
                row.description
            )
            for row in dataframe.itertuples(index=False)
        ]

        cursor.executemany(insert_query, records)
        connection.commit()

        return {
            "message": "Excel data imported successfully.",
            "records_imported": len(records)
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()