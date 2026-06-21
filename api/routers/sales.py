from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from datetime import datetime
from api.database import get_db
from api.models.motor import Motor, MotorStatus
from api.models.invoice import Invoice, InvoiceStatus, PaymentMethod
from api.models.invoice_motor import InvoiceMotor
from api.models.site import Site, SiteType
from api.models.transfer_history import SiteTransferHistory, TransferReason
from api.models.user import User, UserRole
from api.schemas.invoice import InvoiceCreate, InvoiceResponse, InvoiceUpdate, InvoiceApproval
from api.dependencies import get_current_user, require_roles

router = APIRouter()

# --- Showroom Inventory (Dashboard) ---
@router.get("/showroom/{site_id}/motors")
async def list_showroom_motors(site_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Motor).where(Motor.current_site_id == site_id, Motor.status == MotorStatus.READY_FOR_SALE.value))
    motors = result.scalars().all()
    return [
        {
            "motor_id": m.motor_id,
            "serial_number": m.serial_number,
            "model_name": m.model_name,
            "color": m.color,
            "status": m.status,
            "current_site_id": m.current_site_id
        }
        for m in motors
    ]

@router.get("/showroom/{site_id}/sold")
async def list_sold_motors(site_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from datetime import date
    result = await db.execute(
        select(Motor)
        .where(Motor.current_site_id == site_id, Motor.status == MotorStatus.SOLD.value)
    )
    motors = result.scalars().all()
    return [
        {
            "motor_id": m.motor_id,
            "serial_number": m.serial_number,
            "model_name": m.model_name,
            "color": m.color,
        }
        for m in motors
    ]

@router.post("/motors/{motor_id}/status")
async def update_motor_status(motor_id: int, status: str = Body(..., embed=True), db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("ADMIN"))):
    motor = await db.get(Motor, motor_id)
    if not motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    
    if status not in [s.value for s in MotorStatus]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    motor.status = status
    await db.commit()
    return {"message": f"Motor status updated to {status}"}

# --- Create Invoice (Submit for Approval) ---
@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(invoice_data: InvoiceCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("SALES_REP", "ADMIN"))):
    if not invoice_data.motor_ids:
        raise HTTPException(status_code=400, detail="At least one motor must be selected")
    
    motor_results = await db.execute(select(Motor).where(Motor.motor_id.in_(invoice_data.motor_ids)))
    motors = motor_results.scalars().all()
    
    if len(motors) != len(invoice_data.motor_ids):
        raise HTTPException(status_code=400, detail="One or more motors not found")
    
    for motor in motors:
        if motor.status != MotorStatus.READY_FOR_SALE.value:
            raise HTTPException(status_code=400, detail=f"Motor {motor.serial_number} is not available for sale")
        site = await db.get(Site, motor.current_site_id)
        if not site or site.site_type.value != SiteType.SHOWROOM.value:
            raise HTTPException(status_code=400, detail=f"Motor {motor.serial_number} is not at a showroom")
        orphaned_result = await db.execute(
            select(InvoiceMotor).where(InvoiceMotor.motor_id == motor.motor_id)
        )
        orphaned = orphaned_result.scalar_one_or_none()
        if orphaned:
            await db.delete(orphaned)

    site_id = invoice_data.site_id or current_user.assigned_site_id
    if not site_id:
        raise HTTPException(status_code=400, detail="Showroom site required")
    
    site = await db.get(Site, site_id)
    if not site or site.site_type.value != SiteType.SHOWROOM.value:
        raise HTTPException(status_code=400, detail="Invalid showroom site")
    
    invoice_no = invoice_data.invoice_no or f"INV-{site_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    new_invoice = Invoice(
        invoice_no=invoice_no,
        customer_name=invoice_data.customer_name,
        customer_id_number=invoice_data.customer_id_number,
        customer_id_type=invoice_data.customer_id_type,
        customer_id_issue_date=invoice_data.customer_id_issue_date,
        customer_id_expiry_date=invoice_data.customer_id_expiry_date,
        customer_id_authority=invoice_data.customer_id_authority,
        customer_phone=invoice_data.customer_phone,
        customer_alt_phone=invoice_data.customer_alt_phone,
        customer_email=invoice_data.customer_email,
        customer_region=invoice_data.customer_region,
        customer_city=invoice_data.customer_city,
        customer_sub_city=invoice_data.customer_sub_city,
        customer_woreda=invoice_data.customer_woreda,
        customer_house_number=invoice_data.customer_house_number,
        payment_method=invoice_data.payment_method,
        subtotal=invoice_data.subtotal,
        tax=invoice_data.tax,
        total=invoice_data.total,
        sold_by=current_user.user_id,
        site_id=site_id,
        status=InvoiceStatus.PENDING_APPROVAL.value,
        payment_proof_path=invoice_data.payment_proof_path,
    )
    db.add(new_invoice)
    await db.flush()
    
    for motor in motors:
        motor.status = MotorStatus.RESERVED.value
        db.add(InvoiceMotor(invoice_id=new_invoice.invoice_id, motor_id=motor.motor_id))
    
    await db.commit()
    await db.refresh(new_invoice)
    
    return InvoiceResponse(
        invoice_id=new_invoice.invoice_id,
        invoice_no=new_invoice.invoice_no,
        customer_name=new_invoice.customer_name,
        customer_id_number=new_invoice.customer_id_number,
        customer_id_type=new_invoice.customer_id_type,
        customer_id_issue_date=new_invoice.customer_id_issue_date,
        customer_id_expiry_date=new_invoice.customer_id_expiry_date,
        customer_id_authority=new_invoice.customer_id_authority,
        customer_phone=new_invoice.customer_phone,
        customer_alt_phone=new_invoice.customer_alt_phone,
        customer_email=new_invoice.customer_email,
        customer_region=new_invoice.customer_region,
        customer_city=new_invoice.customer_city,
        customer_sub_city=new_invoice.customer_sub_city,
        customer_woreda=new_invoice.customer_woreda,
        customer_house_number=new_invoice.customer_house_number,
        payment_method=new_invoice.payment_method,
        subtotal=new_invoice.subtotal,
        tax=new_invoice.tax,
        total=new_invoice.total,
        sold_at=new_invoice.sold_at,
        sold_by=new_invoice.sold_by,
        site_id=new_invoice.site_id,
        status=new_invoice.status,
        payment_proof_path=new_invoice.payment_proof_path,
    )

# --- List Invoices ---
@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(status: InvoiceStatus | None = None, site_id: int | None = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Invoice).options(
        selectinload(Invoice.seller),
        selectinload(Invoice.site),
        selectinload(Invoice.motor_links).selectinload(InvoiceMotor.motor)
    )
    
    if status:
        query = query.where(Invoice.status == status.value if hasattr(status, 'value') else status)
    
    if site_id:
        query = query.where(Invoice.site_id == site_id)
    elif str(current_user.role.value) == "SALES_REP" and current_user.assigned_site_id:
        query = query.where(Invoice.site_id == current_user.assigned_site_id)
    
    result = await db.execute(query.order_by(Invoice.sold_at.desc()))
    invoices = result.scalars().all()
    
    return [
        InvoiceResponse(
            invoice_id=i.invoice_id,
            invoice_no=i.invoice_no,
            customer_name=i.customer_name,
            customer_id_number=i.customer_id_number,
            customer_id_type=i.customer_id_type,
            customer_id_issue_date=i.customer_id_issue_date,
            customer_id_expiry_date=i.customer_id_expiry_date,
            customer_id_authority=i.customer_id_authority,
            customer_phone=i.customer_phone,
            customer_alt_phone=i.customer_alt_phone,
            customer_email=i.customer_email,
            customer_region=i.customer_region,
            customer_city=i.customer_city,
            customer_sub_city=i.customer_sub_city,
            customer_woreda=i.customer_woreda,
            customer_house_number=i.customer_house_number,
            payment_method=i.payment_method,
            subtotal=i.subtotal,
            tax=i.tax,
            total=i.total,
            sold_at=i.sold_at,
            sold_by=i.sold_by,
            site_id=i.site_id,
            status=i.status,
            payment_proof_path=i.payment_proof_path,
            sold_by_name=i.seller.full_name if i.seller else None,
            site_name=i.site.site_name if i.site else None,
            motor_count=len(i.motor_links),
            motor_links=[
                {
                    "motor_id": link.motor.motor_id,
                    "serial_number": link.motor.serial_number,
                    "model_name": link.motor.model_name,
                    "color": link.motor.color,
                }
                for link in i.motor_links
            ],
        )
        for i in invoices
    ]

# --- Get Invoice Details ---
@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.seller), selectinload(Invoice.site), selectinload(Invoice.motor_links).selectinload(InvoiceMotor.motor))
        .where(Invoice.invoice_id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    motor_links_data = [
        {
            "motor_id": link.motor.motor_id,
            "serial_number": link.motor.serial_number,
            "model_name": link.motor.model_name,
            "color": link.motor.color,
        }
        for link in invoice.motor_links
    ]
    
    return InvoiceResponse(
        invoice_id=invoice.invoice_id,
        invoice_no=invoice.invoice_no,
        customer_name=invoice.customer_name,
        customer_id_number=invoice.customer_id_number,
        customer_id_type=invoice.customer_id_type,
        customer_id_issue_date=invoice.customer_id_issue_date,
        customer_id_expiry_date=invoice.customer_id_expiry_date,
        customer_id_authority=invoice.customer_id_authority,
        customer_phone=invoice.customer_phone,
        customer_alt_phone=invoice.customer_alt_phone,
        customer_email=invoice.customer_email,
        customer_region=invoice.customer_region,
        customer_city=invoice.customer_city,
        customer_sub_city=invoice.customer_sub_city,
        customer_woreda=invoice.customer_woreda,
        customer_house_number=invoice.customer_house_number,
        payment_method=invoice.payment_method,
        subtotal=invoice.subtotal,
        tax=invoice.tax,
        total=invoice.total,
        sold_at=invoice.sold_at,
        sold_by=invoice.sold_by,
        site_id=invoice.site_id,
        status=invoice.status,
        payment_proof_path=invoice.payment_proof_path,
        sold_by_name=invoice.seller.full_name if invoice.seller else None,
        site_name=invoice.site.site_name if invoice.site else None,
        motor_count=len(invoice.motor_links),
        motor_links=motor_links_data,
    )

# --- Approve/Reject Invoice ---
@router.post("/invoices/{invoice_id}/approve")
async def approve_invoice(invoice_id: int, approval: InvoiceApproval, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("ADMIN"))):
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.motor_links).selectinload(InvoiceMotor.motor))
        .where(Invoice.invoice_id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.status != InvoiceStatus.PENDING_APPROVAL.value:
        raise HTTPException(status_code=400, detail="Invoice is not pending approval")
    
    if approval.approve:
        invoice.status = InvoiceStatus.APPROVED.value
        invoice.approved_at = datetime.utcnow()
        invoice.approved_by = current_user.user_id
        
        for link in invoice.motor_links:
            motor = link.motor
            motor.status = MotorStatus.SOLD.value
            transfer = SiteTransferHistory(
                motor_id=motor.motor_id,
                from_site_id=motor.current_site_id,
                to_site_id=None,
                transferred_by=current_user.user_id,
                reason=TransferReason.SALE_TRANSFER.value,
            )
            db.add(transfer)
    else:
        invoice.status = InvoiceStatus.REJECTED.value
        invoice.rejection_reason = approval.rejection_reason
        
        for link in invoice.motor_links:
            motor = link.motor
            motor.status = MotorStatus.READY_FOR_SALE.value
        
        for link in list(invoice.motor_links):
            await db.delete(link)
        invoice.motor_links = []
    
    await db.commit()
    return {"message": f"Invoice {invoice.invoice_no} {'approved' if approval.approve else 'rejected'}"}

# --- Customer Lookup ---
@router.get("/customers")
async def search_customers(query: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Invoice)
        .where(
            (Invoice.customer_name.ilike(f"%{query}%")) |
            (Invoice.customer_phone.ilike(f"%{query}%")) |
            (Invoice.customer_id_number.ilike(f"%{query}%"))
        )
        .options(selectinload(Invoice.motor_links).selectinload(InvoiceMotor.motor))
        .limit(20)
    )
    invoices = result.scalars().all()
    
    return [
        {
            "invoice_id": i.invoice_id,
            "invoice_no": i.invoice_no,
            "customer_name": i.customer_name,
            "customer_phone": i.customer_phone,
            "total": i.total,
            "sold_at": i.sold_at,
            "motors": [link.motor.serial_number for link in i.motor_links],
        }
        for i in invoices
    ]

# --- Daily Sales Report ---
@router.get("/reports/daily")
async def daily_report(site_id: int | None = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from datetime import date, timedelta, datetime
    from sqlalchemy import cast, String, func

    today_start = datetime.combine(date.today(), datetime.min.time())
    tomorrow_start = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())

    where_clause = [Invoice.status == InvoiceStatus.APPROVED.value, Invoice.sold_at >= today_start, Invoice.sold_at < tomorrow_start]
    if site_id:
        where_clause.append(Invoice.site_id == site_id)
    elif str(current_user.role.value) == "SALES_REP" and current_user.assigned_site_id:
        where_clause.append(Invoice.site_id == current_user.assigned_site_id)

    # Get total invoices count
    invoice_count_result = await db.execute(
        select(func.count(Invoice.invoice_id)).where(*where_clause)
    )
    total_invoices = invoice_count_result.scalar() or 0

    # Get total revenue
    revenue_result = await db.execute(
        select(func.sum(Invoice.total)).where(*where_clause)
    )
    revenue_val = revenue_result.scalar()
    total_revenue = float(revenue_val) if revenue_val else 0

    # Get motor count - count motors linked to approved invoices sold today
    motor_where = [Invoice.status == InvoiceStatus.APPROVED.value, Invoice.sold_at >= today_start, Invoice.sold_at < tomorrow_start]
    if site_id:
        motor_where.append(Invoice.site_id == site_id)
    elif str(current_user.role.value) == "SALES_REP" and current_user.assigned_site_id:
        motor_where.append(Invoice.site_id == current_user.assigned_site_id)

    motor_count_result = await db.execute(
        select(func.count(InvoiceMotor.motor_id))
        .join(Invoice, InvoiceMotor.invoice_id == Invoice.invoice_id)
        .where(*motor_where)
    )
    total_motors_sold = motor_count_result.scalar() or 0

    payment_query = select(
        Invoice.payment_method,
        func.sum(Invoice.total).label('total')
    ).where(*where_clause)

    payment_result = await db.execute(payment_query.group_by(Invoice.payment_method))
    payment_rows = payment_result.all()

    payment_breakdown = {}
    for prow in payment_rows:
        pm = prow[0].value if hasattr(prow[0], 'value') else str(prow[0])
        payment_breakdown[pm] = float(prow[1]) if prow[1] else 0

    return {
        "total_invoices": total_invoices,
        "total_motors_sold": total_motors_sold,
        "total_revenue": total_revenue,
        "payment_breakdown": payment_breakdown,
    }


# --- Financial Reports (Admin) ---
@router.get("/reports/financial")
async def financial_report(
    start_date: str | None = None,
    end_date: str | None = None,
    site_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    from datetime import date, timedelta
    from sqlalchemy import cast, String, func
    
    # Get basic invoice data
    query = select(Invoice).where(cast(Invoice.status, String) == "APPROVED")
    
    if start_date:
        query = query.where(Invoice.approved_at >= start_date)
    if end_date:
        query = query.where(Invoice.approved_at <= end_date)
    if site_id:
        query = query.where(Invoice.site_id == site_id)
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    total_revenue = sum(float(i.total) for i in invoices)
    
    # Count motors using SQL
    total_motors = 0
    for i in invoices:
        motor_count_result = await db.execute(
            select(func.count(InvoiceMotor.motor_id)).where(InvoiceMotor.invoice_id == i.invoice_id)
        )
        total_motors += motor_count_result.scalar() or 0
    
    daily_breakdown = {}
    for i in invoices:
        day = i.sold_at.strftime('%Y-%m-%d') if i.sold_at else 'unknown'
        if day not in daily_breakdown:
            daily_breakdown[day] = {"count": 0, "revenue": 0}
        daily_breakdown[day]["revenue"] += float(i.total)
    
    payment_breakdown = {}
    for i in invoices:
        pm = i.payment_method.value if hasattr(i.payment_method, 'value') else str(i.payment_method)
        payment_breakdown[pm] = payment_breakdown.get(pm, 0) + float(i.total)
    
    return {
        "total_invoices": len(invoices),
        "total_motors_sold": total_motors,
        "total_revenue": total_revenue,
        "daily_breakdown": daily_breakdown,
        "payment_breakdown": payment_breakdown,
    }


# --- Upload Payment Proof ---
@router.post("/upload/payment-proof")
async def upload_payment_proof(file: UploadFile = File(...)):
    import shutil
    import os
    from datetime import datetime
    
    upload_dir = "/app/uploads/payment-proofs"
    os.makedirs(upload_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"url": f"/uploads/payment-proofs/{filename}"}


# --- PDF Generation ---
@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from api.services.pdf_generator import generate_invoice_pdf
    
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.motor_links).selectinload(InvoiceMotor.motor),
            selectinload(Invoice.site)
        )
        .where(Invoice.invoice_id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    pdf_dir = "/app/uploads/invoices"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f"{invoice_id}.pdf")
    
    if not os.path.exists(pdf_path):
        motors = [
            {
                "motor_id": link.motor.motor_id,
                "serial_number": link.motor.serial_number or "",
                "model_name": link.motor.model_name or "",
                "color": link.motor.color or "",
                "quantity": 1,
            }
            for link in invoice.motor_links
        ]
        
        invoice_dict = {
            "invoice_id": invoice.invoice_id,
            "invoice_no": invoice.invoice_no,
            "sold_at": str(invoice.sold_at) if invoice.sold_at else "",
            "customer_name": invoice.customer_name or "",
            "customer_id_number": invoice.customer_id_number or "",
            "customer_phone": invoice.customer_phone or "",
            "customer_region": invoice.customer_region or "",
            "customer_city": invoice.customer_city or "",
            "subtotal": float(invoice.subtotal) if invoice.subtotal else 0,
            "tax": float(invoice.tax) if invoice.tax else 0,
            "discount": 0,
            "vat": float(invoice.tax) if invoice.tax else 0,
            "total": float(invoice.total) if invoice.total else 0,
            "payment_method": invoice.payment_method.value if hasattr(invoice.payment_method, 'value') else str(invoice.payment_method),
            "payment_proof_path": invoice.payment_proof_path,
            "business_address": invoice.site.address if invoice.site and invoice.site.address else "Shashamane",
        }
        
        generate_invoice_pdf(invoice_dict, motors)
    
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"invoice-{invoice.invoice_no}.pdf")