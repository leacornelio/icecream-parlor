import os
import psycopg2

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from mangum import Mangum
from pydantic import BaseModel
from typing import Annotated

load_dotenv()

app = FastAPI()
handler = Mangum(app)

BEARER_TOKEN = os.environ['BEARER_TOKEN']
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

connection = psycopg2.connect(
    host = os.environ['DB_HOST'],
    port = os.environ['DB_PORT'],
    user = os.environ['DB_USER'],
    password = os.environ['DB_PASSWORD'],
    database = os.environ['DB_NAME']
)
cursor=connection.cursor()

class Order(BaseModel):
    item: str
    quantity: int

class Stock(BaseModel):
    item: str
    quantity: int

class Feedback(BaseModel):
    comment: str
    rating: int

class Report(BaseModel):
    feedback_summary: str
    average_rating: int

def create_inventory_table():
    try:
        query = """
            CREATE TABLE inventory (
                flavor_id SERIAL PRIMARY KEY,
                flavor VARCHAR(100) NOT NULL UNIQUE,
                quantity INT NOT NULL
            );
        """
        cursor.execute(query)
        connection.commit()
        message = "Sucessfully created 'inventory' table."
    except Exception as e:
        print(e)
        cursor.execute("ROLLBACK")
        connection.commit()
        message = "Failed to create 'inventory' table."
    return message

def create_feedback_table():
    try:
        query = """
                CREATE TABLE feedback (
                    feedback_id SERIAL PRIMARY KEY,
                    comment TEXT NOT NULL,
                    rating INT NOT NULL
            );
        """
        cursor.execute(query)
        connection.commit()
        message = "Sucessfully created 'feedback' table."
    except Exception as e:
        print(e)
        cursor.execute("ROLLBACK")
        connection.commit()
        message = "Failed to create 'feedback' table."
    return message

def create_report_table():
    try:
        query = """
                CREATE TABLE report (
                    report_id SERIAL PRIMARY KEY,
                    feedback_summary TEXT NOT NULL,
                    average_rating INT NOT NULL
            );
        """
        cursor.execute(query)
        connection.commit()
        message = "Sucessfully created 'report' table."
    except Exception as e:
        print(e)
        cursor.execute("ROLLBACK")
        connection.commit()
        message = "Failed to create 'report' table."
    return message

def delete_table(table):
    try:
        query = f"""
            DROP TABLE IF EXISTS {table};
        """
        cursor.execute(query)
        connection.commit()
        message = f"Successfully deleted '{table}' table."
    except Exception as e:
        print(e)
        cursor.execute("ROLLBACK")
        connection.commit()
        message = f"Failed to delete '{table}' table."
    return message

@app.post("/order")
def place_order(order: Order, token: Annotated[str, Depends(oauth2_scheme)]):
    if token != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        flavor = order.item.lower()
        query = f"""
            WITH updated AS (
                UPDATE inventory
                SET quantity = quantity - {order.quantity}
                WHERE flavor = '{flavor}' AND quantity >= {order.quantity}
                RETURNING flavor
            )
            SELECT flavor FROM updated;
        """
        cursor.execute(query)
        connection.commit()
    except Exception as e:
        print(e)
        cursor.execute("ROLLBACK")
        connection.commit()
    return {}

@app.post("/restock")
def restock_inventory(stock: Stock, token: Annotated[str, Depends(oauth2_scheme)]):
    if token != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        flavor = stock.item.lower()
        query = f"""
            INSERT INTO inventory (flavor, quantity)
            VALUES ('{flavor}', {stock.quantity})
            ON CONFLICT (flavor) DO UPDATE
            SET quantity = inventory.quantity + EXCLUDED.quantity;
        """
        cursor.execute(query)
        connection.commit()
    except Exception as e:
        print(e)
        cursor.execute("ROLLBACK")
        connection.commit()
    return {}

@app.post("/feedback")
def submit_feedback(feedback: Feedback, token: Annotated[str, Depends(oauth2_scheme)]):
    if token != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        query = f"""
            INSERT INTO feedback (comment, rating)
            VALUES ('{feedback.comment}', {feedback.rating});
        """
        cursor.execute(query)
        connection.commit()
    except Exception as e:
        print(e)
        cursor.execute("ROLLBACK")
        connection.commit()
    return {}

@app.post("/report")
def submit_report(report: Report, token: Annotated[str, Depends(oauth2_scheme)]):
    if token != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        query = f"""
            INSERT INTO report (feedback_summary, average_rating)
            VALUES ('{report.feedback_summary}', {report.average_rating});
        """
        cursor.execute(query)
        connection.commit()
    except Exception as e:
        print(e)
        cursor.execute("ROLLBACK")
        connection.commit()
    return {}

@app.get("/inventory")
def fetch_inventory(token: Annotated[str, Depends(oauth2_scheme)]):
    if token != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        query = """
            SELECT flavor, quantity FROM inventory;
        """
        cursor.execute(query)
        connection.commit()
        
        # Fetch all results
        inventory = cursor.fetchall()
        
        # Convert the results into a list
        inventory = [{"item": item[0], "quantity": item[1]} for item in inventory]
        output = {"items": inventory}
    except Exception as e:
        print(e)
        cursor.execute("ROLLBACK")
        connection.commit()
        output = {"items": []}
    return output

@app.get("/menu")
def fetch_menu(token: Annotated[str, Depends(oauth2_scheme)]):
    if token != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        query = f"""
            SELECT flavor FROM inventory WHERE quantity > 0;
        """
        cursor.execute(query)
        connection.commit()

        # Fetch all results
        menu = cursor.fetchall()
        
        # Convert to a list
        menu = [item[0] for item in menu]
        output = {"flavors": menu}
    except Exception as e:
        print(e)
        cursor.execute("ROLLBACK")
        connection.commit()
        output = {"flavors": []}
    return output

@app.get("/feedback")
def fetch_feedback(token: Annotated[str, Depends(oauth2_scheme)]):
    if token != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        query = """
            SELECT comment, rating FROM feedback;
        """
        cursor.execute(query)
        connection.commit()

        # Fetch all the results
        feedbacks = cursor.fetchall()
        
        # Convert the results into a list
        feedbacks = [{'comment': feedback[0], 'rating': feedback[1]} for feedback in feedbacks]
        output = {"feedback": feedbacks}
    except Exception as e:
        print(e)
        cursor.execute("ROLLBACK")
        connection.commit()
        output = {"feedback": []}
    return output

@app.get("/report")
def fetch_report(token: Annotated[str, Depends(oauth2_scheme)]):
    if token != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        query = """
            SELECT feedback_summary, average_rating FROM report;
        """
        cursor.execute(query)
        connection.commit()

        # Fetch all the results
        reports = cursor.fetchall()
        
        # Convert the results into a list
        reports = [{'feedback_summary': report[0], 'average_rating': report[1]} for report in reports]
        output = {"report": reports}
    except Exception as e:
        print(e)
        cursor.execute("ROLLBACK")
        connection.commit()
        output = {"report": []}
    return output