from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional

class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = Field(None, min_length=4, max_length=20)
    expires_at: Optional[datetime] = None

class LinkUpdate(BaseModel):
    original_url: HttpUrl

class LinkInfo(BaseModel):
    original_url: str
    short_code: str
    created_at: datetime
    expires_at: Optional[datetime]
    clicks: int
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True