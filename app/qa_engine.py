""" LLM + Retrieval QA chain"""

import os
from typing import Any, Dict

from transformers import pipeline

from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain

from app.storage import get_retriever

PROVIDER = os.getenv('LLM_PROVIDER', 'openrouter')
OPENROUTER_MODEL = 'qwen/qwen3-32B:free'

def _load_llm():
    """Выбор и загрузка LLM (локально или через openrouter)"""

    if PROVIDER == 'openrouter':
        if not os.getenv('OPENROUTER_API_KEY'):
            raise RuntimeError('OPENROUTER_API_KEY не установлен')
        
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=OPENROUTER_MODEL,
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url='https://openrouter.ai/api/v1',
        )

    elif PROVIDER == 'local':
        pipe = pipeline(
            'text-generation',
            model='Qwen/Qwen3-7B-Chat',
            device_map='auto',
            max_new_tokens=512,
            do_sample=False,
        )
        return HuggingFacePipeline(pipeline=pipe)

_llm = _load_llm()

### Prompt ###

_system_prompt = 'Ты работаешь только с загруженным документом. Отвечай кратко, только по сути документа и на русском языке'
_prompt = ChatPromptTemplate.from_messages([
    ('system', _system_prompt),
    ('human', 'Контекст:\n{context}\n\nВопрос: {input}'),
])

_combine_chain = create_stuff_documents_chain(llm=_llm, prompt=_prompt)

### 
def answer_question(file_id: str, question: str) -> str:
    """Возврат финального ответа LLM для указанного документа"""

    retriever = get_retriever(file_id)
    qa_chain = create_retrieval_chain(retriever, _combine_chain)
    result: Dict[str, Any] = qa_chain.invoke({'input': question})

    return result['answer']