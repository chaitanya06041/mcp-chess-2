from mcp.server.fastmcp import FastMCP
import json
import os
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

mcp = FastMCP("Employee")
JSON_FILE_PATH = "data.json"

class Employee(BaseModel):
    id: int = Field(..., description="Unique employee ID")
    name: str = Field(..., min_length=1, description="Employee's full name")
    job_role: str = Field(..., min_length=1, description="Employee's job role")
    department: str = Field(..., min_length=1, description="Employee's department")
    salary: float = Field(..., gt=0, description="Employee's salary")

def read_db() -> List[dict]:
    if not os.path.exists(JSON_FILE_PATH):
        return []
    with open(JSON_FILE_PATH, 'r') as f:
        return json.load(f)

def write_db(data: List[dict]):
    with open(JSON_FILE_PATH, 'w') as f:
        json.dump(data, f, indent=4)


@mcp.tool()
def add_employee(name: str, job_role: str, department: str, salary: float) -> str:
    """Add a new employee. ID is generated automatically.
    Args:
        name (str): Employee's full name.
        job_role (str): Employee's job role.
        department (str): Employee's department.
        salary (float): Employee's salary (must be greater than 0).
    Returns:
        str: Success message with new employee ID or error message."""
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
    """
    Retrieve employee details by ID.
    Args:
        employee_id (int): The unique ID of the employee to retrieve.
    """
    employees = read_db()
    employee = next((e for e in employees if e["id"] == employee_id), None)
    
    if not employee:
        return f"Error: Employee with ID {employee_id} not found."
    return json.dumps(employee, indent=2)

@mcp.tool()
def update_employee(employee_id: int, name: str, job_role: str, department: str, salary: float) -> str:
    """
    Update an existing employee's details while keeping the same ID.
    Args:
        employee_id (int): The unique ID of the employee to update.
        name (str): Updated full name of the employee.
        job_role (str): Updated job role of the employee.
        department (str): Updated department of the employee.
        salary (float): Updated salary of the employee (must be greater than 0).
    """
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
    """
    Remove an employee from the records by ID.
    Args:
        employee_id (int): The unique ID of the employee to delete.
    """
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

@mcp.resource("employees://ids")
def get_employee_ids() -> str:
    """Get a list of all existing employee IDs."""
    employees = read_db()
    ids = [emp["id"] for emp in employees]
    return f"Available Employee IDs: {ids}"

if __name__ == "__main__":
    if not os.path.exists(JSON_FILE_PATH):
        write_db([])
    mcp.run()