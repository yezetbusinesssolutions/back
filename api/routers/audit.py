from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from api.database import get_db
from api.models.motor import Motor
from api.models.transfer_history import SiteTransferHistory
from api.models.delivery import Delivery
from api.dependencies import get_current_user

router = APIRouter()

@router.get("/motor/{motor_id}/history")
async def motor_history(motor_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    motor_result = await db.execute(select(Motor).where(Motor.motor_id == motor_id))
    motor = motor_result.scalar_one_or_none()
    if not motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    transfer_result = await db.execute(
        select(SiteTransferHistory).where(SiteTransferHistory.motor_id == motor_id).order_by(SiteTransferHistory.transferred_at)
    )
    transfers = transfer_result.scalars().all()
    return {
        "motor": {
            "motor_id": motor.motor_id,
            "serial_number": motor.serial_number,
            "model_name": motor.model_name,
            "status": motor.status
        },
        "transfers": [
            {
                "transfer_id": t.transfer_id,
                "reason": t.reason,
                "from_site_id": t.from_site_id,
                "to_site_id": t.to_site_id,
                "transferred_at": t.transferred_at,
                "transferred_by": t.transferred_by
            }
            for t in transfers
        ]
    }

@router.get("/delivery/{delivery_no}/cartons")
async def delivery_cartons(delivery_no: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    result = await db.execute(select(Delivery).where(Delivery.delivery_no == delivery_no))
    delivery = result.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    motor_result = await db.execute(select(Motor).where(Motor.delivery_id == delivery.delivery_id))
    motors = motor_result.scalars().all()
    return {
        "delivery_no": delivery.delivery_no,
        "received_at": delivery.received_at,
        "cartons": [
            {
                "motor_id": m.motor_id,
                "serial_number": m.serial_number,
                "model_name": m.model_name,
                "status": m.status
            }
            for m in motors
        ]
    }
