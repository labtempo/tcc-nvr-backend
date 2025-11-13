from pydantic import BaseModel, Field

class MediaMTXWebhookPayload(BaseModel):
    absolute_path: str = Field(alias="absolutePath")
    duration_ns: int = Field(alias="duration")
