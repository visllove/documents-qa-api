import concurrent.futures
import aiofiles

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from fastapi import UploadFile, HTTPException, status
from docx import Document as DocxDocument

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DIR = DATA_DIR / "chroma"
CHROMA_DIR.mkdir(exist_ok=True)

EMBEDDING_MODEL = 'intfloat/multilingual-e5-base'

_embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={'local_files_only': True}, 
    encode_kwargs={'normalize_embeddings': True},
)

_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)

_store: Chroma = Chroma(
    collection_name='sapsan_docs',
    embedding_function=_embeddings,
    persist_directory=str(CHROMA_DIR)
)

@dataclass  
class DocumentInfo:
    file_path: Path
    status: str
    pages: List[Document] | None = None
    

documents: Dict[str, DocumentInfo] = {}

# пул для задач с векторизацией документов
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


async def save_docx(file_id: str, upload: UploadFile) -> Path:
    """Сохранение файла со статусом building без ожидания векторной обработки"""

    file_path = DATA_DIR / f'{file_id}.docx'

    # Сохранение файла
    async with aiofiles.open(file_path, 'wb') as out:
        while chunk := await upload.read(1 << 20):
            await out.write(chunk)
    
    documents[file_id] = DocumentInfo(file_path=file_path, status='building')
    return file_path


def build_index_async(file_id: str, file_path: Path) -> None:
    """Обертка для функции _build_index, постановка задачи в пул"""

    _executor.submit(_build_index, file_id, file_path)


def _build_index(file_id: str, file_path: Path) -> None:
    """ Извлечение текста, создание эмбеддингов, запись в Chroma"""

    try:
        docx_obj = DocxDocument(file_path)
        full_text = '\n'.join(p.text for p in docx_obj.paragraphs if p.text.strip())

        pages = _splitter.create_documents([full_text])
        
        for page in pages:
            page.metadata['file_id'] = file_id
        
        _store.add_documents(pages)
        documents[file_id].status = 'ready'
        documents[file_id].pages = pages
    except Exception:
        documents[file_id].status = 'failed'
        raise


def exists(file_id: str) -> bool:
    return file_id in documents


def is_ready(file_id: str) -> bool:
    return exists(file_id) and documents[file_id].status == 'ready'


def ensure_ready(file_id: str) -> None:
    if not is_ready(file_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Index building')


def get_retriever(file_id: str):
    ensure_ready(file_id)
    return _store.as_retriever(search_kwargs={'k': 4, 'filter': {'file_id': file_id}})


### Загрузка списка документов из сохраненных файлов

def preload_documents_from_chroma() -> None:
    """Считываем все file_id из Chroma и заполняем словарь documents, чтобы api помнил о загруженных ранее документах"""
    seen: set[str] = set()
    for md in _store.get()['metadatas']:
        file_id = md.get('file_id')
        if not file_id or file_id in seen:
            continue

        path = DATA_DIR / f'{file_id}.docx'
        if path.exists():
            documents[file_id] = DocumentInfo(file_path=path, status='ready')
            seen.add(file_id)