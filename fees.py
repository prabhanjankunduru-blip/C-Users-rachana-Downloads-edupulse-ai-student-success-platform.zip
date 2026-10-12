from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3
import random
from datetime import datetime
from app.db.database import get_connection

router = APIRouter(prefix="/api/fees", tags=["fees"])

class FeePaymentRequest(BaseModel):
    student_id: str
    fee_id: int
    payment_method: str
    amount: float
    card_or_upi_info: Optional[str] = "UPI/GPay"

@router.get("/{student_id}")
def get_student_fees(student_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT fp.*, s.name as student_name, s.roll_no, s.department
    FROM fee_payments fp
    JOIN students s ON fp.student_id = s.id
    WHERE fp.student_id = ?
    ORDER BY 
        CASE fp.status 
            WHEN 'Overdue' THEN 1 
            WHEN 'Pending' THEN 2 
            ELSE 3 
        END, fp.due_date ASC
    """, (student_id,))

    rows = [dict(r) for r in cursor.fetchall()]

    total_pending = sum(r["amount"] for r in rows if r["status"] in ["Pending", "Overdue"])
    total_paid = sum(r["amount"] for r in rows if r["status"] == "Paid")

    conn.close()

    return {
        "student_id": student_id,
        "total_pending": total_pending,
        "total_paid": total_paid,
        "invoices": rows
    }

@router.post("/pay")
def pay_fee(req: FeePaymentRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fee_payments WHERE id = ? AND student_id = ?", (req.fee_id, req.student_id))
    fee = cursor.fetchone()
    if not fee:
        conn.close()
        raise HTTPException(status_code=404, detail="Fee invoice record not found")

    if fee["status"] == "Paid":
        conn.close()
        return {
            "success": True,
            "message": "This fee invoice is already cleared!",
            "invoice": dict(fee)
        }

    txn_id = f"TXN_{req.student_id}_{random.randint(100000, 999999)}"
    pay_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE fee_payments
    SET status = 'Paid',
        transaction_id = ?,
        payment_date = ?,
        payment_method = ?
    WHERE id = ?
    """, (txn_id, pay_date, req.payment_method, req.fee_id))

    conn.commit()

    cursor.execute("SELECT * FROM fee_payments WHERE id = ?", (req.fee_id,))
    updated_fee = dict(cursor.fetchone())
    conn.close()

    return {
        "success": True,
        "message": f"Payment of ₹{req.amount:,.2f} for '{updated_fee['title']}' successful!",
        "transaction_id": txn_id,
        "payment_date": pay_date,
        "receipt": {
            "invoice_number": updated_fee["invoice_number"],
            "fee_type": updated_fee["fee_type"],
            "title": updated_fee["title"],
            "amount": updated_fee["amount"],
            "transaction_id": txn_id,
            "payment_method": req.payment_method,
            "payment_date": pay_date,
            "status": "PAID"
        }
    }

@router.get("/receipt/{invoice_no}")
def get_fee_receipt(invoice_no: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT fp.*, s.name as student_name, s.roll_no, s.department, s.email
    FROM fee_payments fp
    JOIN students s ON fp.student_id = s.id
    WHERE fp.invoice_number = ?
    """, (invoice_no,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Invoice receipt not found")
    return dict(row)
