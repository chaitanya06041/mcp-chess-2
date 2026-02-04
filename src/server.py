from mcp.server.fastmcp import FastMCP
import json
import os
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

# --- Dynamic Path Configuration ---
# Use /tmp for cloud environments (like watsonx) to bypass Permission Errors.
# On your MacBook, it will default to your Documents folder.
if os.name == 'posix' and not os.path.exists(os.path.expanduser("~/Documents")):
    JSON_FILE_PATH = "/tmp/employee_data.json"
else:
    JSON_FILE_PATH = os.path.expanduser("~/Documents/employee_data.json")

mcp = FastMCP("Employee")

# --- Pydantic Models ---
class Employee(BaseModel):
    id: int = Field(..., description="Unique employee ID")
    name: str = Field(..., min_length=1, description="Employee's full name")
    job_role: str = Field(..., min_length=1, description="Employee's job role")
    department: str = Field(..., min_length=1, description="Employee's department")
    salary: float = Field(..., gt=0, description="Employee's salary")

# --- Helper functions for File I/O ---
def read_db() -> List[dict]:
    if not os.path.exists(JSON_FILE_PATH):
        return []
    try:
        with open(JSON_FILE_PATH, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        return []

def write_db(data: List[dict]):
    with open(JSON_FILE_PATH, 'w') as f:
        json.dump(data, f, indent=4)

# --- MCP Tools ---

@mcp.tool()
def add_employee(name: str, job_role: str, department: str, salary: float) -> str:
    """Add a new employee with auto-generated ID."""
    employees = read_db()
    new_id = max([emp["id"] for emp in employees if isinstance(emp, dict)], default=0) + 1
    new_employee = {
        "id": new_id, "name": name, "job_role": job_role, 
        "department": department, "salary": salary
    }
    employees.append(new_employee)
    write_db(employees)
    return f"Employee added successfully with ID: {new_id}"

@mcp.tool()
def list_employees() -> str:
    """List all employees."""
    return json.dumps(read_db(), indent=2)

@mcp.tool()
def get_employee(employee_id: int) -> str:
    """Retrieve employee details by ID."""
    employees = read_db()
    employee = next((e for e in employees if e["id"] == employee_id), None)
    return json.dumps(employee, indent=2) if employee else f"Error: ID {employee_id} not found."

@mcp.resource("employees://ids")
def get_employee_ids() -> str:
    """Get a list of all existing employee IDs."""
    ids = [emp["id"] for emp in read_db() if isinstance(emp, dict)]
    return f"Available Employee IDs: {ids}"

def main():
    # Ensure the directory exists before attempting to write
    db_dir = os.path.dirname(JSON_FILE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        
    if not os.path.exists(JSON_FILE_PATH):
        write_db([])
    mcp.run()

if __name__ == "__main__":
    main()