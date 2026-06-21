from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime
from api.database import get_db
from api.models.motor import Motor, MotorStatus
from api.models.delivery import Delivery
from api.models.site import Site, SiteType
from api.models.transfer_history import SiteTransferHistory, TransferReason
from api.models.user import User
from api.schemas.motor import MotorCreate, MotorUpdate, MotorResponse
from api.schemas.delivery import DeliveryCreate, DeliveryResponse
from api.dependencies import get_current_user, require_roles

router = APIRouter()

@router.post("/deliveries", response_model=DeliveryResponse)
async def create_delivery(delivery_data: DeliveryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("RECEIVER", "ADMIN"))):
    new_delivery = Delivery(**delivery_data.dict(), received_by=current_user.user_id)
    db.add(new_delivery)
    await db.commit()
    await db.refresh(new_delivery)
    return new_delivery

@router.get("/deliveries", response_model=list[DeliveryResponse])
async def list_deliveries(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Delivery))
    return result.scalars().all()

@router.get("/deliveries/{delivery_id}", response_model=DeliveryResponse)
async def get_delivery(delivery_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Delivery).where(Delivery.delivery_id == delivery_id))
    delivery = result.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery

@router.get("/deliveries/{delivery_id}/motors", response_model=list[MotorResponse])
async def get_delivery_motors(delivery_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Motor).where(Motor.delivery_id == delivery_id))
    return result.scalars().all()

@router.post("/deliveries")
async def create_delivery(delivery_data: dict = Body(...), db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("RECEIVER", "ADMIN"))):
    delivery_no = delivery_data.get("delivery_no") or f"DEL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    new_delivery = Delivery(
        delivery_no=delivery_no,
        received_at_site_id=delivery_data.get("site_id"),
        received_by=current_user.user_id,
        supplier_name=delivery_data.get("supplier_name"),
        notes=delivery_data.get("notes"),
    )
    db.add(new_delivery)
    await db.commit()
    await db.refresh(new_delivery)
    return {"delivery_id": new_delivery.delivery_id, "delivery_no": new_delivery.delivery_no, "received_at": new_delivery.received_at}

@router.post("/receive-carton", response_model=MotorResponse)
async def receive_carton(motor_data: MotorCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("RECEIVER", "ADMIN"))):
    delivery_no = motor_data.delivery_no or f"DEL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    result = await db.execute(select(Delivery).where(Delivery.delivery_no == delivery_no))
    delivery = result.scalar_one_or_none()
    if not delivery:
        delivery = Delivery(delivery_no=delivery_no, received_at_site_id=motor_data.current_site_id, received_by=current_user.user_id)
        db.add(delivery)
        await db.flush()
    motor_dict = motor_data.dict(exclude={"delivery_id", "delivery_no"})
    new_motor = Motor(**motor_dict, delivery_id=delivery.delivery_id, received_by=current_user.user_id)
    db.add(new_motor)
    await db.flush()
    transfer = SiteTransferHistory(
        motor_id=new_motor.motor_id,
        to_site_id=motor_data.current_site_id,
        transferred_by=current_user.user_id,
        reason=TransferReason.RECEIVED.value,
    )
    db.add(transfer)
    await db.commit()
    await db.refresh(new_motor)
    return new_motor

# --- Motors ---
@router.get("/motors", response_model=list[MotorResponse])
async def list_motors(status: str | None = None, site_id: int | None = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Motor)
    if status:
        query = query.where(Motor.status == status)
    if site_id:
        query = query.where(Motor.current_site_id == site_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/motors/{motor_id}", response_model=MotorResponse)
async def get_motor(motor_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Motor).where(Motor.motor_id == motor_id))
    motor = result.scalar_one_or_none()
    if not motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    return motor

@router.put("/motors/{motor_id}", response_model=MotorResponse)
async def update_motor(motor_id: int, motor_data: MotorUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("ADMIN", "ASSEMBLER"))):
    result = await db.execute(select(Motor).where(Motor.motor_id == motor_id))
    motor = result.scalar_one_or_none()
    if not motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    for key, value in motor_data.dict(exclude_unset=True).items():
        setattr(motor, key, value)
    await db.commit()
    await db.refresh(motor)
    return motor

@router.post("/start-assembly/{motor_id}", response_model=MotorResponse)
async def start_assembly(motor_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("ASSEMBLER", "ADMIN"))):
    result = await db.execute(select(Motor).where(Motor.motor_id == motor_id))
    motor = result.scalar_one_or_none()
    if not motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    if motor.status != MotorStatus.RECEIVED.value:
        raise HTTPException(status_code=400, detail="Motor must be in Received status")
    motor.status = MotorStatus.IN_PROGRESS.value
    motor.assembly_started = datetime.utcnow()
    motor.assembled_by = current_user.user_id
    await db.commit()
    await db.refresh(motor)
    return motor

@router.post("/complete-assembly/{motor_id}", response_model=MotorResponse)
async def complete_assembly(motor_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("ASSEMBLER", "ADMIN"))):
    result = await db.execute(select(Motor).where(Motor.motor_id == motor_id))
    motor = result.scalar_one_or_none()
    if not motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    if motor.status != MotorStatus.IN_PROGRESS.value:
        raise HTTPException(status_code=400, detail="Motor must be In Progress")
    motor.status = MotorStatus.READY_FOR_SALE.value
    motor.assembled_at = datetime.utcnow()
    await db.commit()
    await db.refresh(motor)
    return motor

@router.post("/mark-defective/{motor_id}", response_model=MotorResponse)
async def mark_defective(motor_id: int, reason: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("ASSEMBLER", "ADMIN"))):
    result = await db.execute(select(Motor).where(Motor.motor_id == motor_id))
    motor = result.scalar_one_or_none()
    if not motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    if motor.status in [MotorStatus.SOLD.value, MotorStatus.DEFECTIVE.value]:
        raise HTTPException(status_code=400, detail="Motor cannot be marked defective")
    motor.status = MotorStatus.DEFECTIVE.value
    motor.defect_reason = reason
    await db.commit()
    await db.refresh(motor)
    return motor

@router.post("/transfer-to-showroom/{motor_id}")
async def transfer_to_showroom(motor_id: int, body: dict = Body(...), db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("ASSEMBLER", "ADMIN", "RECEIVER"))):
    destination_site_id = body.get("destination_site_id")
    result = await db.execute(select(Motor).where(Motor.motor_id == motor_id))
    motor = result.scalar_one_or_none()
    if not motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    if motor.status != MotorStatus.READY_FOR_SALE.value:
        raise HTTPException(status_code=400, detail="Motor must be Ready for Sale")
    source_site_result = await db.execute(select(Site).where(Site.site_id == motor.current_site_id))
    source_site = source_site_result.scalar_one_or_none()
    if not source_site or source_site.site_type.value != SiteType.ASSEMBLY_PLANT.value:
        raise HTTPException(status_code=400, detail="Source site must be Assembly Plant")
    dest_site_result = await db.execute(select(Site).where(Site.site_id == destination_site_id))
    dest_site = dest_site_result.scalar_one_or_none()
    if not dest_site or dest_site.site_type.value != SiteType.SHOWROOM.value:
        raise HTTPException(status_code=400, detail="Destination must be Showroom")
    original_site_id = motor.current_site_id
    motor.current_site_id = destination_site_id
    transfer = SiteTransferHistory(
        motor_id=motor.motor_id,
        from_site_id=original_site_id,
        to_site_id=destination_site_id,
        transferred_by=current_user.user_id,
        reason=TransferReason.STOCK_MOVE.value
    )
    db.add(transfer)
    await db.commit()
    return {"message": "Transferred successfully"}

@router.get("/ready-for-transfer", response_model=list[MotorResponse])
async def list_ready_for_transfer(site_id: int | None = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Motor).where(Motor.status == MotorStatus.READY_FOR_SALE.value)
    if site_id:
        result = await db.execute(select(Site).where(Site.site_id == site_id))
        site = result.scalar_one_or_none()
        if site and site.site_type.value == SiteType.ASSEMBLY_PLANT.value:
            query = query.where(Motor.current_site_id == site_id)
    else:
        assembly_plant_subquery = select(Site.site_id).where(Site.site_type == SiteType.ASSEMBLY_PLANT.value)
        query = query.where(Motor.current_site_id.in_(assembly_plant_subquery))
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/motors/{motor_id}/history")
async def get_motor_history(motor_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(SiteTransferHistory).where(SiteTransferHistory.motor_id == motor_id).order_by(SiteTransferHistory.transferred_at))
    transfers = result.scalars().all()
    return [
        {
            "transfer_id": t.transfer_id,
            "from_site_id": t.from_site_id,
            "to_site_id": t.to_site_id,
            "transferred_at": t.transferred_at,
            "transferred_by": t.transferred_by,
            "reason": t.reason.value,
        }
        for t in transfers
    ]

@router.get("/transfers")
async def list_all_transfers(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(SiteTransferHistory)
        .options(selectinload(SiteTransferHistory.motor), selectinload(SiteTransferHistory.from_site), selectinload(SiteTransferHistory.to_site), selectinload(SiteTransferHistory.transferred_by_user))
        .order_by(SiteTransferHistory.transferred_at.desc())
        .limit(50)
    )
    transfers = result.scalars().unique().all()
    return [
        {
            "transfer_id": t.transfer_id,
            "motor_id": t.motor_id,
            "motor_serial": t.motor.serial_number if t.motor else None,
            "motor_model": t.motor.model_name if t.motor else None,
            "from_site_id": t.from_site_id,
            "from_site_name": t.from_site.site_name if t.from_site else None,
            "from_site_type": t.from_site.site_type.value if t.from_site else None,
            "to_site_id": t.to_site_id,
            "to_site_name": t.to_site.site_name if t.to_site else None,
            "to_site_type": t.to_site.site_type.value if t.to_site else None,
            "transferred_at": t.transferred_at,
            "transferred_by": t.transferred_by,
            "transferred_by_name": t.transferred_by_user.full_name if t.transferred_by_user else None,
            "reason": t.reason.value,
        }
        for t in transfers
    ]
