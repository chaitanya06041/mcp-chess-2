from mcp.server.fastmcp import FastMCP
import json
import os
import tempfile
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

# --- Dynamic Path Configuration ---
# Uses /tmp for cloud environments (like watsonx) to avoid Permission Errors
if os.name == 'posix' and not os.path.exists(os.path.expanduser("~/Documents")):
    JSON_FILE_PATH = "/tmp/employee_data.json"
else:
    # Default path for local development on your MacBook
    JSON_FILE_PATH = os.path.expanduser("~/Documents/employee_data.json")

mcp = FastMCP("Employee")

# --- Pydantic Models ---
class Employee(BaseModel):
    """Employee data model with validation."""
    id: int = Field(..., description="Unique employee ID")
    name: str = Field(..., min_length=1, description="Employee's full name")
    job_role: str = Field(..., min_length=1, description="Employee's job role")
    department: str = Field(..., min_length=1, description="Employee's department")
    salary: float = Field(..., gt=0, description="Employee's salary")

# --- Helper functions for File I/O ---
def read_db() -> List[dict]:
    """Reads the JSON database safely."""
    if not os.path.exists(JSON_FILE_PATH):
        return []
    try:
        with open(JSON_FILE_PATH, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        return []

def write_db(data: List[dict]):
    """Writes the JSON database with proper formatting."""
    with open(JSON_FILE_PATH, 'w') as f:
        json.dump(data, f, indent=4)

# --- MCP Tools (CRUD Operations) ---

@mcp.tool()
def add_employee(name: str, job_role: str, department: str, salary: float) -> str:
    """Add a new employee. ID is generated automatically."""
    employees = read_db()
    
    # Generate ID: Find max ID and add 1
    new_id = max([emp["id"] for emp in employees], default=0) + 1
    
    new_employee = {
        "id": new_id,
        "name": name,
        "job_role": job_role,
        "department": department,
        "salary": salary
    }
    
    employees.append(new_employee)
    write_db(employees)
    return f"Employee added successfully with ID: {new_id}"

@mcp.tool()
def get_employee(employee_id: int) -> str:
    """Retrieve employee details by ID."""
    employees = read_db()
    employee = next((e for e in employees if e["id"] == employee_id), None)
    
    if not employee:
        return f"Error: Employee with ID {employee_id} not found."
    return json.dumps(employee, indent=2)

@mcp.tool()
def update_employee(employee_id: int, name: str, job_role: str, department: str, salary: float) -> str:
    """Update an existing employee's details while keeping the same ID."""
    employees = read_db()
    for emp in employees:
        if emp["id"] == employee_id:
            emp.update({
                "name": name,
                "job_role": job_role,
                "department": department,
                "salary": salary
            })
            write_db(employees)
            return f"Employee {employee_id} updated successfully."
    
    return f"Error: Employee with ID {employee_id} not found."

@mcp.tool()
def delete_employee(employee_id: int) -> str:
    """Remove an employee from the records by ID."""
    employees = read_db()
    updated_list = [e for e in employees if e["id"] != employee_id]
    
    if len(updated_list) == len(employees):
        return f"Error: Employee with ID {employee_id} not found."
    
    write_db(updated_list)
    return f"Employee {employee_id} deleted successfully."

@mcp.tool()
def list_employees() -> str:
    """List all employees and their details."""
    employees = read_db()
    return json.dumps(employees, indent=2)

# --- MCP Resources ---

@mcp.resource("employees://ids")
def get_employee_ids() -> str:
    """Get a list of all existing employee IDs."""
    employees = read_db()
    ids = [emp["id"] for emp in employees if isinstance(emp, dict) and "id" in emp]
    return f"Available Employee IDs: {ids}"

# --- Execution ---

def main():
    """Main entry point for the server."""
    # Ensure the directory exists before writing
    db_dir = os.path.dirname(JSON_FILE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        
    if not os.path.exists(JSON_FILE_PATH):
        write_db([])
    mcp.run()

if __name__ == "__main__":
    main()