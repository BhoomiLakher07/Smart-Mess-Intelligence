
const API_URL = "http://127.0.0.1:8000";

let expenseChart = null;
let categoryChart = null;
let dailyExpenseChart = null;


// ==========================================
// LOAD DASHBOARD
// ==========================================

async function loadDashboard() {
    try {
        const endpoints = [
            "/analytics/summary",
            "/analytics/categories",
            "/analytics/daily",
            "/analytics/budget-utilization"
        ];

        const responses = await Promise.all(
            endpoints.map(endpoint => fetch(`${API_URL}${endpoint}`))
        );

        if (responses.some(response => !response.ok)) {
            throw new Error("One or more dashboard APIs failed.");
        }

        const [
            studentData,
            categoryData,
            dailyData,
            budgetData
        ] = await Promise.all(
            responses.map(response => response.json())
        );

        updateCards(studentData, budgetData);
        updateTable(studentData, budgetData);
        updateBudgetInsights(studentData, budgetData);
        updateChart(studentData);
        updateCategoryChart(categoryData);
        updateDailyExpenseChart(dailyData);

    } catch (error) {
        console.error("Dashboard error:", error);

        document.getElementById("studentTable").innerHTML = `
            <tr>
                <td colspan="6">
                    Unable to load data from API. Check that the backend is running.
                </td>
            </tr>
        `;
    }
}


// ==========================================
// SUMMARY CARDS
// ==========================================

function updateCards(data) {
    const totalStudents = data.length;

    const totalBudget = data.reduce(
        (sum, student) => sum + Number(student.monthly_budget || 0),
        0
    );

    const totalExpense = data.reduce(
        (sum, student) => sum + Number(student.total_expense || 0),
        0
    );

    const remainingBudget = data.reduce(
        (sum, student) => sum + Number(student.remaining_budget || 0),
        0
    );

    const utilization = totalBudget > 0
        ? (totalExpense / totalBudget) * 100
        : 0;

    document.getElementById("totalStudents").textContent = totalStudents;
    document.getElementById("totalBudget").textContent = formatCurrency(totalBudget);
    document.getElementById("totalExpense").textContent = formatCurrency(totalExpense);
    document.getElementById("remainingBudget").textContent = formatCurrency(remainingBudget);
    document.getElementById("budgetUtilization").textContent =
        `${utilization.toFixed(2)}%`;
}


// ==========================================
// STUDENT TABLE
// ==========================================

function updateTable(data) {
    const table = document.getElementById("studentTable");
    table.innerHTML = "";

    if (!data.length) {
        table.innerHTML = `
            <tr><td colspan="6">No students found.</td></tr>
        `;
        return;
    }

    data.forEach(student => {
        const budget = Number(student.monthly_budget || 0);
        const expense = Number(student.total_expense || 0);
        const remaining = Number(student.remaining_budget || 0);

        const utilization = budget > 0
            ? (expense / budget) * 100
            : 0;

        let status;
        let statusClass;

        if (expense >= budget && budget > 0) {
            status = "Budget Exceeded";
            statusClass = "exceeded";
        } else if (budget > 0 && expense >= budget * 0.8) {
            status = "Near Limit";
            statusClass = "near";
        } else {
            status = "Within Budget";
            statusClass = "within";
        }

        const progressWidth = Math.min(Math.max(utilization, 0), 100);
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${escapeHTML(student.name)}</td>
            <td>${formatCurrency(budget)}</td>
            <td>${formatCurrency(expense)}</td>
            <td>${formatCurrency(remaining)}</td>
            <td>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill"
                             style="width: ${progressWidth}%"></div>
                    </div>
                    <div class="progress-text">
                        ${utilization.toFixed(2)}% used
                    </div>
                </div>
            </td>
            <td>
                <span class="badge ${statusClass}">
                    ${status}
                </span>
            </td>
        `;

        table.appendChild(row);
    });
}


// ==========================================
// BUDGET INTELLIGENCE
// ==========================================

function updateBudgetInsights(data) {
    const totalBudget = data.reduce(
        (sum, student) => sum + Number(student.monthly_budget || 0),
        0
    );

    const totalExpense = data.reduce(
        (sum, student) => sum + Number(student.total_expense || 0),
        0
    );

    const utilization = totalBudget > 0
        ? (totalExpense / totalBudget) * 100
        : 0;

    const highestSpender = data.reduce((highest, student) => {
        if (
            highest === null ||
            Number(student.total_expense || 0) >
            Number(highest.total_expense || 0)
        ) {
            return student;
        }
        return highest;
    }, null);

    const nearLimit = data.filter(student => {
        const budget = Number(student.monthly_budget || 0);
        const expense = Number(student.total_expense || 0);
        return budget > 0 && expense >= budget * 0.8 && expense < budget;
    }).length;

    const overBudget = data.filter(student => {
        const budget = Number(student.monthly_budget || 0);
        return budget > 0 &&
            Number(student.total_expense || 0) >= budget;
    }).length;

    let budgetStatus;

    if (overBudget > 0) {
        budgetStatus = `${overBudget} student(s) over budget`;
    } else if (nearLimit > 0) {
        budgetStatus = `${nearLimit} student(s) near limit`;
    } else {
        budgetStatus = "All students within budget";
    }

    document.getElementById("overallUtilization").textContent =
        `${utilization.toFixed(2)}%`;

    document.getElementById("highestSpender").textContent =
        highestSpender
            ? `${highestSpender.name} — ${formatCurrency(Number(highestSpender.total_expense || 0))}`
            : "No expenses";

    document.getElementById("nearLimitStudents").textContent = nearLimit;
    document.getElementById("budgetStatus").textContent = budgetStatus;
}


// ==========================================
// STUDENT EXPENSE CHART
// ==========================================

function updateChart(data) {
    const canvas = document.getElementById("expenseChart");
    if (!canvas) return;

    if (expenseChart) expenseChart.destroy();

    expenseChart = new Chart(canvas.getContext("2d"), {
        type: "bar",
        data: {
            labels: data.map(student => student.name),
            datasets: [{
                label: "Total Expense (₹)",
                data: data.map(student => Number(student.total_expense || 0))
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: true } },
            scales: { y: { beginAtZero: true } }
        }
    });
}


// ==========================================
// CATEGORY EXPENSE CHART
// ==========================================

function updateCategoryChart(data) {
    const canvas = document.getElementById("categoryChart");
    if (!canvas) return;

    if (categoryChart) categoryChart.destroy();

    categoryChart = new Chart(canvas.getContext("2d"), {
        type: "doughnut",
        data: {
            labels: data.map(item => item.category),
            datasets: [{
                label: "Expense by Category",
                data: data.map(item => Number(item.total_expense || 0))
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true, position: "bottom" }
            }
        }
    });
}


// ==========================================
// DAILY EXPENSE TREND
// ==========================================

function updateDailyExpenseChart(data) {
    const canvas = document.getElementById("dailyExpenseChart");
    if (!canvas) return;

    if (dailyExpenseChart) dailyExpenseChart.destroy();

    dailyExpenseChart = new Chart(canvas.getContext("2d"), {
        type: "line",
        data: {
            labels: data.map(item => item.expense_date),
            datasets: [{
                label: "Daily Expense (₹)",
                data: data.map(item => Number(item.total_expense || 0)),
                tension: 0.3,
                fill: false
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: { y: { beginAtZero: true } }
        }
    });
}


// ==========================================
// EXCEL IMPORT
// ==========================================

const importForm = document.getElementById("importForm");
const excelFileInput = document.getElementById("excelFile");
const importButton = document.getElementById("importButton");
const importStatus = document.getElementById("importStatus");

function showImportStatus(message, type) {
    importStatus.textContent = message;
    importStatus.classList.remove("success", "error", "loading");

    if (type) {
        importStatus.classList.add(type);
    }
}

importForm.addEventListener("submit", async event => {
    event.preventDefault();

    const file = excelFileInput.files[0];

    if (!file) {
        showImportStatus("Please choose an Excel file first.", "error");
        return;
    }

    if (!file.name.toLowerCase().endsWith(".xlsx")) {
        showImportStatus("Please upload an .xlsx Excel file.", "error");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    importButton.disabled = true;
    showImportStatus("Importing Excel data...", "loading");

    try {
        const response = await fetch(`${API_URL}/import/expenses`, {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.detail || "Unable to import the Excel file."
            );
        }

        showImportStatus(
            `Success! ${result.records_imported} expense record(s) imported.`,
            "success"
        );

        excelFileInput.value = "";

        await loadDashboard();

    } catch (error) {
        console.error("Excel import error:", error);

        showImportStatus(
            error.message || "Import failed. Check the backend server.",
            "error"
        );
    } finally {
        importButton.disabled = false;
    }
});


// ==========================================
// EXCEL EXPORT
// ==========================================

document.getElementById("exportButton").addEventListener("click", async () => {
    const exportButton = document.getElementById("exportButton");

    exportButton.disabled = true;
    showImportStatus("Preparing Excel export...", "loading");

    try {
        const response = await fetch(`${API_URL}/export/expenses`);

        if (!response.ok) {
            let message = "Unable to export expenses.";
            try {
                const result = await response.json();
                message = result.detail || message;
            } catch (_) {}
            throw new Error(message);
        }

        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);
        const link = document.createElement("a");

        link.href = downloadUrl;
        link.download = "expenses.xlsx";
        document.body.appendChild(link);
        link.click();
        link.remove();

        URL.revokeObjectURL(downloadUrl);

        showImportStatus("Excel export downloaded successfully.", "success");

    } catch (error) {
        console.error("Excel export error:", error);
        showImportStatus(
            error.message || "Export failed. Check the backend server.",
            "error"
        );
    } finally {
        exportButton.disabled = false;
    }
});


// ==========================================
// HELPERS
// ==========================================

function formatCurrency(amount) {
    return `₹${Number(amount || 0).toLocaleString("en-IN", {
        maximumFractionDigits: 2
    })}`;
}

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}


// ==========================================
// START DASHBOARD
// ==========================================

loadDashboard();