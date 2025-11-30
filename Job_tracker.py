import sqlite3
import csv
from datetime import datetime

DB_NAME = "jobs.db"


def get_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_NAME)
    return conn


def create_table():
    """Create the jobs table if it does not exist."""
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
    print("Table created successfully")


# ---------- CORE ACTIONS ----------

def add_job():
    """Ask user for job details and insert into the database."""
    print("\n=== Add New Job Application ===")

    company = input("Company name: ").strip()
    role = input("Role / Position: ").strip()
    location = input("Location (optional): ").strip()
    applied_date = input("Applied date (e.g. 2025-11-30): ").strip()
    status = input(
        "Status (Applied / Online Test / Interview / Rejected / Offer): ").strip()
    salary_input = input(
        "Salary (optional, just press Enter if unknown): ").strip()
    notes = input("Notes (optional): ").strip()

    if company == "" or role == "":
        print("❌ Company and Role are required. Job not saved.")
        return

    # Convert salary safely
    if salary_input == "":
        salary = None
    else:
        try:
            salary = float(salary_input)
        except ValueError:
            print("Invalid salary entered. Saving salary as empty.")
            salary = None

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

    print("✅ Job application saved successfully!")


def view_all_jobs():
    """Fetch and display all job applications from the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, company, role, location, applied_date, status, salary
        FROM jobs
        ORDER BY id DESC;
        """
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("\nNo job applications found yet.")
        return

    print("\n=== All Job Applications ===")
    print(
        f"{'ID':<4} {'Company':<20} {'Role':<20} {'Location':<12} "
        f"{'Date':<12} {'Status':<12} {'Salary':<10}"
    )
    print("-" * 95)

    for row in rows:
        job_id, company, role, location, applied_date, status, salary = row

        location = location if location else "-"
        applied_date = applied_date if applied_date else "-"
        status = status if status else "-"
        salary_str = f"{salary:.0f}" if salary is not None else "-"

        print(
            f"{job_id:<4} {company[:18]:<20} {role[:18]:<20} {location[:10]:<12} "
            f"{applied_date:<12} {status[:10]:<12} {salary_str:<10}"
        )


def view_by_status():
    """View applications filtered by a specific status."""
    print("\n=== View Applications by Status ===")
    status_input = input(
        "Enter status (Applied / Online Test / Interview / Rejected / Offer): ").strip()

    if status_input == "":
        print("No status entered. Returning to menu.")
        return

    status_clean = status_input.lower()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, company, role, location, applied_date, status, salary
        FROM jobs
        WHERE LOWER(status) = ?;
        """,
        (status_clean,)
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(f"\nNo applications found with status: {status_input}")
        return

    print(f"\n=== Applications with status: {status_input} ===")
    print(
        f"{'ID':<4} {'Company':<20} {'Role':<20} {'Location':<12} "
        f"{'Date':<12} {'Status':<12} {'Salary':<10}"
    )
    print("-" * 95)

    for row in rows:
        job_id, company, role, location, applied_date, status, salary = row

        location = location if location else "-"
        applied_date = applied_date if applied_date else "-"
        status = status if status else "-"
        salary_str = f"{salary:.0f}" if salary is not None else "-"

        print(
            f"{job_id:<4} {company[:18]:<20} {role[:18]:<20} {location[:10]:<12} "
            f"{applied_date:<12} {status[:10]:<12} {salary_str:<10}"
        )


def show_stats():
    """Show summary statistics about your applications."""
    conn = get_connection()
    cursor = conn.cursor()

    # total applications
    cursor.execute("SELECT COUNT(*) FROM jobs;")
    total = cursor.fetchone()[0]

    # count by status
    cursor.execute(
        """
        SELECT status, COUNT(*)
        FROM jobs
        GROUP BY status;
        """
    )
    status_counts = cursor.fetchall()

    # top companies
    cursor.execute(
        """
        SELECT company, COUNT(*)
        FROM jobs
        GROUP BY company
        ORDER BY COUNT(*) DESC
        LIMIT 5;
        """
    )
    top_companies = cursor.fetchall()

    conn.close()

    print("\n=== Application Summary ===")
    print(f"Total applications: {total}")

    if total == 0:
        return

    print("\nBy status:")
    for status, count in status_counts:
        label = status if status else "Unknown"
        print(f"  {label}: {count}")

    print("\nTop companies you applied to:")
    for company, count in top_companies:
        print(f"  {company}: {count}")


# ---------- UPDATE / DELETE / SEARCH / EXPORT ----------

def get_job_by_id(job_id):
    """Return a single job row by ID, or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, company, role, location, applied_date, status, salary, notes
        FROM jobs
        WHERE id = ?;
        """,
        (job_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row


def update_job():
    """Update status, salary, date or notes for a job."""
    print("\n=== Update Job Application ===")
    job_id_input = input("Enter Job ID to update: ").strip()

    if not job_id_input.isdigit():
        print("Invalid ID. Must be a number.")
        return

    job_id = int(job_id_input)
    job = get_job_by_id(job_id)

    if job is None:
        print(f"No job found with ID {job_id}")
        return

    _, company, role, location, applied_date, status, salary, notes = job

    print(f"\nCurrent values for Job {job_id}:")
    print(f"  Company : {company}")
    print(f"  Role    : {role}")
    print(f"  Location: {location}")
    print(f"  Date    : {applied_date}")
    print(f"  Status  : {status}")
    print(f"  Salary  : {salary}")
    print(f"  Notes   : {notes}")

    print("\nLeave blank to keep existing value.")

    new_status = input("New status: ").strip()
    new_date = input("New applied date: ").strip()
    new_salary_input = input("New salary: ").strip()
    new_notes = input("New notes: ").strip()

    if new_status == "":
        new_status = status
    if new_date == "":
        new_date = applied_date
    if new_notes == "":
        new_notes = notes

    if new_salary_input == "":
        new_salary = salary
    else:
        try:
            new_salary = float(new_salary_input)
        except ValueError:
            print("Invalid salary entered. Keeping old salary.")
            new_salary = salary

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jobs
        SET status = ?, applied_date = ?, salary = ?, notes = ?
        WHERE id = ?;
        """,
        (new_status, new_date, new_salary, new_notes, job_id)
    )

    conn.commit()
    conn.close()
    print("✅ Job updated successfully!")


def delete_job():
    """Delete a job by ID."""
    print("\n=== Delete Job Application ===")
    job_id_input = input("Enter Job ID to delete: ").strip()

    if not job_id_input.isdigit():
        print("Invalid ID. Must be a number.")
        return

    job_id = int(job_id_input)
    job = get_job_by_id(job_id)

    if job is None:
        print(f"No job found with ID {job_id}")
        return

    _, company, role, *_ = job
    confirm = input(
        f"Are you sure you want to delete {company} - {role}? (y/n): ").strip().lower()
    if confirm != "y":
        print("Deletion cancelled.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE id = ?;", (job_id,))
    conn.commit()
    conn.close()
    print("🗑️ Job deleted successfully!")


def search_jobs():
    """Search jobs by keyword in company, role or location."""
    print("\n=== Search Jobs ===")
    keyword = input(
        "Enter keyword to search (company/role/location): ").strip().lower()

    if keyword == "":
        print("No keyword entered. Returning to menu.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    like_pattern = f"%{keyword}%"

    cursor.execute(
        """
        SELECT id, company, role, location, applied_date, status, salary
        FROM jobs
        WHERE LOWER(company) LIKE ?
           OR LOWER(role) LIKE ?
           OR LOWER(location) LIKE ?
        ORDER BY id DESC;
        """,
        (like_pattern, like_pattern, like_pattern)
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(f"\nNo jobs found matching: {keyword}")
        return

    print(f"\n=== Search results for '{keyword}' ===")
    print(
        f"{'ID':<4} {'Company':<20} {'Role':<20} {'Location':<12} "
        f"{'Date':<12} {'Status':<12} {'Salary':<10}"
    )
    print("-" * 95)

    for row in rows:
        job_id, company, role, location, applied_date, status, salary = row

        location = location if location else "-"
        applied_date = applied_date if applied_date else "-"
        status = status if status else "-"
        salary_str = f"{salary:.0f}" if salary is not None else "-"

        print(
            f"{job_id:<4} {company[:18]:<20} {role[:18]:<20} {location[:10]:<12} "
            f"{applied_date:<12} {status[:10]:<12} {salary_str:<10}"
        )


def export_to_csv():
    """Export all jobs to a CSV file."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, company, role, location, applied_date, status, salary, notes
        FROM jobs
        ORDER BY id DESC;
        """
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("\nNo jobs to export.")
        return

    filename = f"job_applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Company", "Role", "Location",
                        "Applied Date", "Status", "Salary", "Notes"])
        writer.writerows(rows)

    print(f"📁 Exported {len(rows)} jobs to {filename}")


# ---------- MENU & MAIN LOOP ----------

def main_menu():
    """Show menu and return the user's choice."""
    print("\n=== Job Application Tracker v3 ===")
    print("1. Add new job application")
    print("2. View all applications")
    print("3. View applications by status")
    print("4. Show summary / stats")
    print("5. Update a job")
    print("6. Delete a job")
    print("7. Search jobs")
    print("8. Export to CSV")
    print("9. Exit")

    choice = input("Enter your choice (1-9): ").strip()
    return choice


def main():
    """Main app loop."""
    print(">>> Starting Job Tracker v3")
    create_table()  # ensure table exists

    while True:
        choice = main_menu()

        if choice == "1":
            add_job()
        elif choice == "2":
            view_all_jobs()
        elif choice == "3":
            view_by_status()
        elif choice == "4":
            show_stats()
        elif choice == "5":
            update_job()
        elif choice == "6":
            delete_job()
        elif choice == "7":
            search_jobs()
        elif choice == "8":
            export_to_csv()
        elif choice == "9":
            print("Exiting... Bye!")
            break
        else:
            print("Invalid choice, please enter a number from 1 to 9.")


if __name__ == "__main__":
    main()
