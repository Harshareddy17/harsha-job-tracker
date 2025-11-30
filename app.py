import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

DB_NAME = "jobs.db"


# ---------- DATABASE HELPERS ----------

def get_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_NAME)
    return conn


def create_table():
    """Create the jobs table if it does not exist (same as CLI app)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            location TEXT,
            applied_date TEXT,
            status TEXT,
            salary REAL,
            notes TEXT
        );
        """
    )

    conn.commit()
    conn.close()


def fetch_all_jobs():
    """Return all jobs as a pandas DataFrame."""
    conn = get_connection()
    query = """
        SELECT id, company, role, location, applied_date, status, salary, notes
        FROM jobs
        ORDER BY id DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def insert_job(company, role, location, applied_date, status, salary, notes):
    """Insert a new job row into the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO jobs (company, role, location, applied_date, status, salary, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        (company, role, location, applied_date, status, salary, notes)
    )

    conn.commit()
    conn.close()


def get_job_by_id(job_id: int):
    """Return one job row as dict, or None."""
    conn = get_connection()
    query = """
        SELECT id, company, role, location, applied_date, status, salary, notes
        FROM jobs
        WHERE id = ?;
    """
    df = pd.read_sql_query(query, conn, params=(job_id,))
    conn.close()
    if df.empty:
        return None
    return df.iloc[0]


def update_job(job_id, status, applied_date, salary, notes):
    """Update fields for one job."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jobs
        SET status = ?, applied_date = ?, salary = ?, notes = ?
        WHERE id = ?;
        """,
        (status, applied_date, salary, notes, job_id)
    )

    conn.commit()
    conn.close()


def delete_job(job_id):
    """Delete job by id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE id = ?;", (job_id,))
    conn.commit()
    conn.close()


# ---------- STREAMLIT PAGES ----------

def page_dashboard():
    st.header("📊 Dashboard – Applications Overview")

    df = fetch_all_jobs()

    if df.empty:
        st.info("No job applications yet. Add some from the **Add Job** page.")
        return

    # --- FILTERS (SIDEBAR) ---
    st.sidebar.subheader("🔎 Filters")

    # status filter
    all_statuses = sorted(df["status"].dropna().unique().tolist())
    status_filter = st.sidebar.multiselect(
        "Status",
        options=all_statuses,
        default=all_statuses,
    )

    # company filter
    companies = sorted(df["company"].dropna().unique().tolist())
    company_filter = st.sidebar.multiselect(
        "Company",
        options=companies,
        default=companies,
    )

    # search text (company / role / location)
    search_text = st.sidebar.text_input("Search (company / role / location)")

    # apply filters
    filtered = df.copy()

    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]
    if company_filter:
        filtered = filtered[filtered["company"].isin(company_filter)]
    if search_text.strip():
        s = search_text.strip().lower()
        mask = (
            filtered["company"].str.lower().str.contains(s)
            | filtered["role"].str.lower().str.contains(s)
            | filtered["location"].fillna("").str.lower().str.contains(s)
        )
        filtered = filtered[mask]

    # --- TOP METRICS ---
    col1, col2, col3 = st.columns(3)
    total_apps = len(df)
    total_filtered = len(filtered)
    num_interview = (df["status"].str.lower() == "interview").sum()
    num_offer = (df["status"].str.lower() == "offer").sum()

    col1.metric("Total applications", total_apps)
    col2.metric("Filtered shown", total_filtered)
    col3.metric("Offers", int(num_offer))

    st.subheader("📋 Applications (filtered)")
    st.dataframe(filtered, use_container_width=True, height=350)

    # --- SIMPLE STATS & CHARTS ---
    st.subheader("📈 Status breakdown")
    status_counts = (
        df["status"]
        .fillna("Unknown")
        .value_counts()
        .rename_axis("status")
        .reset_index(name="count")
    )
    st.bar_chart(status_counts, x="status", y="count")

    st.subheader("🏢 Top companies by applications")
    company_counts = (
        df["company"]
        .fillna("Unknown")
        .value_counts()
        .head(10)
        .rename_axis("company")
        .reset_index(name="count")
    )
    st.bar_chart(company_counts, x="company", y="count")


def page_add_job():
    st.header("➕ Add New Job Application")

    with st.form("add_job_form"):
        col1, col2 = st.columns(2)

        with col1:
            company = st.text_input("Company*", "")
            role = st.text_input("Role / Position*", "")
            location = st.text_input("Location", "")

        with col2:
            applied_date = st.text_input("Applied Date (e.g. 2025-11-30)", "")
            status = st.selectbox(
                "Status",
                ["Applied", "Online Test", "Interview",
                    "Rejected", "Offer", "Other"],
                index=0,
            )
            salary_input = st.text_input("Salary (optional)", "")

        notes = st.text_area("Notes (optional)", "")

        submitted = st.form_submit_button("Save Job")

    if submitted:
        if company.strip() == "" or role.strip() == "":
            st.error("Company and Role are required.")
        else:
            # salary handling
            if salary_input.strip() == "":
                salary = None
            else:
                try:
                    salary = float(salary_input.strip())
                except ValueError:
                    st.warning("Invalid salary. Saving as empty.")
                    salary = None

            insert_job(
                company.strip(),
                role.strip(),
                location.strip(),
                applied_date.strip(),
                status.strip(),
                salary,
                notes.strip(),
            )
            st.success("✅ Job saved successfully!")


def page_manage_jobs():
    st.header("🛠 Manage Jobs (Update / Delete)")

    df = fetch_all_jobs()
    if df.empty:
        st.info("No jobs yet.")
        return

    st.write("Select a job to update or delete:")

    # show a simple table to see ids
    st.dataframe(df[["id", "company", "role", "status"]],
                 use_container_width=True, height=220)

    job_id_list = df["id"].tolist()
    selected_id = st.selectbox("Choose Job ID", job_id_list)

    job = get_job_by_id(int(selected_id))
    if job is None:
        st.error("Selected job not found.")
        return

    st.markdown(
        f"### Editing Job ID {job['id']} – {job['company']} / {job['role']}")

    col_left, col_right = st.columns(2)

    with col_left:
        new_status = st.selectbox(
            "Status",
            ["Applied", "Online Test", "Interview", "Rejected", "Offer", "Other"],
            index=0 if pd.isna(job["status"]) else 0,
            help="Update the current status.",
        )
        # pre-select current status if present
        if not pd.isna(job["status"]) and job["status"] in new_status:
            pass  # not perfect, but simple; we keep selected option list small

        new_date = st.text_input("Applied Date", job["applied_date"] or "")

    with col_right:
        salary_str = "" if pd.isna(job["salary"]) else str(job["salary"])
        new_salary_input = st.text_input("Salary", salary_str)
        new_notes = st.text_area("Notes", job["notes"] or "", height=120)

    col_u, col_d = st.columns(2)

    if col_u.button("💾 Save changes"):
        # handle salary
        if new_salary_input.strip() == "":
            new_salary = None
        else:
            try:
                new_salary = float(new_salary_input.strip())
            except ValueError:
                st.warning("Invalid salary. Keeping old value.")
                new_salary = job["salary"]

        update_job(
            job_id=int(job["id"]),
            status=new_status,
            applied_date=new_date.strip(),
            salary=new_salary,
            notes=new_notes.strip(),
        )
        st.success("✅ Job updated!")
        st.experimental_rerun()

    if col_d.button("🗑 Delete this job"):
        delete_job(int(job["id"]))
        st.success("🗑 Job deleted!")
        st.experimental_rerun()


# ---------- MAIN APP ----------

def main():
    st.set_page_config(
        page_title="Harsha Job Tracker",
        page_icon="📋",
        layout="wide",
    )

    # simple dark-ish background tweak
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top left, #0f172a, #020617);
            color: #e5e7eb;
        }
        .block-container {
            padding-top: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    create_table()

    st.sidebar.title("Harsha Job Tracker")
    page = st.sidebar.radio(
        "Navigate",
        ["Dashboard", "Add Job", "Manage Jobs"],
        index=0,
    )

    if page == "Dashboard":
        page_dashboard()
    elif page == "Add Job":
        page_add_job()
    elif page == "Manage Jobs":
        page_manage_jobs()


if __name__ == "__main__":
    main()
