from pydantic import BaseModel

class BillBase(BaseModel):
    vendor: str | None = None
    date: str | None = None
    due_date: str | None = None
    amount: float | None = None
    currency: str | None = None
    category: str | None = None
    status: str | None = None
    blob_name: str | None = None
    message_id: str | None = None

class BillOut(BillBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True
