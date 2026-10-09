from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.database import get_connection

from backend.analytics import (
    get_student_summary,
    get_category_summary,
    get_daily_expense_summary,
    get_budget_utilization
)

from backend.excel import (
    export_expenses_to_excel,
    import_expenses_from_excel
)


# ==========================================
# CREATE FASTAPI APP
# ==========================================

app = FastAPI(
    title="Smart Mess & Expense Intelligence Platform"
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {
        "message": "Smart Mess API is running"
    }


# ==========================================
# STUDENTS
# ==========================================

@app.get("/students")
def get_students():

    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            student_id,
            name,
            monthly_budget
        FROM students
    """)

    students = cursor.fetchall()

    cursor.close()
    connection.close()

    return students


# ==========================================
# STUDENT EXPENSE SUMMARY
# ==========================================

@app.get("/analytics/summary")
def summary():

    return get_student_summary()


# ==========================================
# CATEGORY EXPENSES
# ==========================================

@app.get("/analytics/categories")
def categories():

    return get_category_summary()


# ==========================================
# DAILY EXPENSES
# ==========================================

@app.get("/analytics/daily")
def daily_expenses():

    return get_daily_expense_summary()


# ==========================================
# BUDGET UTILIZATION
# ==========================================

@app.get("/analytics/budget-utilization")
def budget_utilization():

    return get_budget_utilization()


# ==========================================
# EXPORT EXPENSES TO EXCEL
# ==========================================

@app.get("/export/expenses")
def export_expenses():

    excel_file = export_expenses_to_excel()

    return StreamingResponse(
        excel_file,
        media_type=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                "attachment; filename=expenses.xlsx"
        }
    )


# ==========================================
# IMPORT EXPENSES FROM EXCEL
# ==========================================

@app.post("/import/expenses")
async def import_expenses(
    file: UploadFile = File(...)
):

    # --------------------------------------
    # CHECK FILE TYPE
    # --------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )


    if not file.filename.lower().endswith(
        (".xlsx", ".xls")
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid file format. "
                "Please upload an Excel file."
            )
        )


    try:

        # ----------------------------------
        # READ UPLOADED FILE
        # ----------------------------------

        file_content = await file.read()

        # ----------------------------------
        # IMPORT INTO DATABASE
        # ----------------------------------

        result = import_expenses_from_excel(
            file_content
        )

        return result


    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to import Excel file: "
                + str(error)
            )
        )