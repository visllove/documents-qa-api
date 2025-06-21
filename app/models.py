from enum import Enum
from typing import Annotated, Optional
import uuid

from pydantic import BaseModel, Field, StringConstraints


StrictStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class FileUploadResponse(BaseModel):
    """Ответ на загрузку .docx"""

    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class QuestionRequest(BaseModel):
    """Тело запроса для POST /files/{id}/questions"""

    question: StrictStr


class QuestionResponse(BaseModel):
    """Ответ с question_id"""
    question_id: str


class AnswerStatus(str, Enum):
    pending = 'pending'
    running = 'running'
    done = 'done'
    failed = 'failed'

class AnswerResponse(BaseModel):
    """Ответ на get /questions/{id}"""
    status: AnswerStatus
    answer: Optional[str] = None