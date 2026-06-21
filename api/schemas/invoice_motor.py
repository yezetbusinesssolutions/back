from pydantic import BaseModel


class InvoiceMotorCreate(BaseModel):
    invoice_id: int
    motor_id: int


class InvoiceMotorResponse(BaseModel):
    invoice_id: int
    motor_id: int
    serial_number: str | None = None
    model_name: str | None = None
    color: str | None = None

    class Config:
        from_attributes = True
