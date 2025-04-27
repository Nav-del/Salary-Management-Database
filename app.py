from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Password@123",  # Change if needed
        database="sem2SQl"
    )

@app.route('/employees', methods=['POST'])
def search_employees():
    try:
        data = request.get_json()
        search = data.get('employees', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if search:
            cursor.execute("""
                SELECT * FROM employees
                WHERE CONCAT(FirstName, ' ', LastName) LIKE %s OR EmployeeID = %s
            """, (f"%{search}%", search))
        else:
            cursor.execute("SELECT * FROM employees")

        results = cursor.fetchall()
        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/add_employee', methods=['POST'])
def add_employee():
    try:
        data = request.form
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO Employees 
            (EmployeeID, FirstName, LastName, DateOfBirth, Gender, Address, PhoneNumber, Email, HireDate, DepartmentID, JobTitleID, ManagerID)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data['EmployeeID'],
            data['FirstName'],
            data['LastName'],
            data['DateOfBirth'],
            data['Gender'],
            data['Address'],
            data['PhoneNumber'],
            data['Email'],
            data['HireDate'],
            data['DepartmentID'],
            data['JobTitleID'],
            data['ManagerID'] if data['ManagerID'] else None
        )

        cursor.execute(query, values)
        conn.commit()
        return jsonify({"message": "Employee added successfully."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/delete_employee', methods=['POST'])
def delete_employee():
    try:
        data = request.get_json()
        emp_id = data.get('EmployeeID')

        if not emp_id:
            return jsonify({'error': 'EmployeeID is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Employees WHERE EmployeeID = %s", (emp_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'message': 'No employee found with the given ID'}), 404

        return jsonify({'message': f'Employee with ID {emp_id} deleted successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/get_salary', methods=['POST'])
def get_salary():
    try:
        data = request.get_json()
        employee_id = data.get('EmployeeID')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT s.SalaryID, s.EmployeeID, s.SalaryAmount,
                   IFNULL(SUM(b.BonusAmount), 0) AS TotalBonuses,
                   IFNULL(SUM(d.DeductionAmount), 0) AS TotalDeductions,
                   (s.SalaryAmount + IFNULL(SUM(b.BonusAmount), 0) - IFNULL(SUM(d.DeductionAmount), 0)) AS FinalSalary
            FROM Salaries s
            LEFT JOIN Paychecks p ON s.EmployeeID = p.EmployeeID
            LEFT JOIN Bonuses b ON p.PaycheckID = b.PaycheckID
            LEFT JOIN Deductions d ON p.PaycheckID = d.PaycheckID
            WHERE s.EmployeeID = %s
            GROUP BY s.SalaryID
        """
        cursor.execute(query, (employee_id,))
        result = cursor.fetchall()

        return jsonify(result if result else {"error": "No salary data found."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@app.route('/salary_summary', methods=['GET'])
def salary_summary():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                (SELECT IFNULL(SUM(SalaryAmount), 0) FROM Salaries) AS TotalSalary,
                (SELECT IFNULL(AVG(SalaryAmount), 0) FROM Salaries) AS AverageSalary,
                (SELECT COUNT(*) FROM Employees) AS EmployeeCount,
                (SELECT IFNULL(SUM(DeductionAmount), 0) FROM Deductions) AS TotalDeductions,
                (SELECT IFNULL(SUM(TaxAmount), 0) FROM Employee_Taxes) AS TotalTaxes
        """

        cursor.execute(query)
        result = cursor.fetchone()

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()



# Run Flask only once
if __name__ == '__main__':
    app.run(debug=True)
