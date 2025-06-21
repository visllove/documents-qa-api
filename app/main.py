import logging
from typing import Dict, Any
from uuid import uuid4
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, status

from app.models import FileUploadResponse, QuestionRequest, QuestionResponse, AnswerResponse, AnswerStatus
from app import storage, qa_engine

from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.preload_documents_from_chroma()
    yield


api = FastAPI(title='Sapsan Documents QA', lifespan=lifespan)

logger = logging.getLogger(__name__)

answers: Dict[str, Dict[str, Any]] = {}



@api.post('/files', response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail='Поддерживаются только .docx-файлы')
    
    file_id = str(uuid4())

    try:
        await storage.save_docx(file_id, file)
    finally:
        await file.close()

    return FileUploadResponse(file_id=file_id)


@api.post('/files/{file_id}/questions', response_model=QuestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def ask_questions(file_id: str, q: QuestionRequest, bg: BackgroundTasks):
    if not storage.exists(file_id):
        raise HTTPException(status_code=404, detail='Файл не найден')
    
    question_id = str(uuid4())
    answers[question_id] = {'status': AnswerStatus.pending, 'answer': None}

    def _process():
        answers[question_id]['status'] = AnswerStatus.running
        try:
            answer = qa_engine.answer_question(file_id, q.question)
            answers[question_id] = {'status': AnswerStatus.done, 'answer': answer}
        except Exception as e:
            logger.exception(f'Failed to answer question {question_id}', exc_info=e)
            answers[question_id] = {'status': AnswerStatus.failed, 'answer': 'internal error'}
    
    bg.add_task(_process)
    return QuestionResponse(question_id=question_id)


@api.get('/questions/{question_id}', response_model=AnswerResponse)
async def get_answer(question_id: str):
    if question_id not in answers:
        raise HTTPException(status_code=404, detail='question_id не найден')
    return AnswerResponse(**answers[question_id])