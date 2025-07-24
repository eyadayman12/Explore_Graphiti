import re
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
import json

class ArabicTextPreprocessing:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.diacritics_pattern = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640\uf0b7]')
    
    def load_pdf(self) -> str:

        loader = PyPDFLoader(self.pdf_path)
        documents = loader.load()
        return documents

    def basic_clean(self, text: str) -> str:
        
        text = self.diacritics_pattern.sub('', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        text = re.sub(r'^\d+\s+', '', text, flags=re.MULTILINE)
        
        return text
    
    def process_pdf_for_rag(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Load and process PDF for RAG system"""
        
        print("Loading PDF...")
        documents = self.load_pdf()
        
        print("Cleaning text...")
        cleaned_docs = []
        for i, doc in enumerate(documents):
            cleaned_content = self.basic_clean(doc.page_content)
            
            if len(cleaned_content.strip()) < 50:
                continue
                
            cleaned_doc = Document(
                page_content=cleaned_content,
                metadata={
                    'page': i + 1,
                    'source': self.pdf_path,
                    'char_count': len(cleaned_content)
                }
            )
            cleaned_docs.append(cleaned_doc)
        
        print("Splitting into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=['\n\n', '\n', '؟', '!', '،', ' '] 
        )
        
        chunks = text_splitter.split_documents(cleaned_docs)
        
        for i, chunk in enumerate(chunks):
            chunk.metadata['chunk_id'] = i
            chunk.metadata['chunk_size'] = len(chunk.page_content)
        
        print(f"Created {len(chunks)} chunks from {len(cleaned_docs)} pages")
        return chunks
    

Preprocessor = ArabicTextPreprocessing("Arabic.pdf")
chunked_documents = Preprocessor.process_pdf_for_rag(chunk_size=1500, chunk_overlap=250)

llm = ChatOpenAI(model = "gpt-4.1-mini")

name_prompt = "اكتب عنوان مكون من كلمتين او ثلاث كلمات فقط ردك يجب أن يكون إجابة وحيدة صريحة فقط بدون أي مهاترات للفقرة الأتية:"
description_prompt = "اكتب وصف من سطر واحد فقط بأقل عدد كلمات ممكنة ردك يجب أن يكون إجابة وحيدة صريحة فقط بدون أي مهاترات للفقرة الأتية:"
epsiodes = []

for i in chunked_documents:
    epsiodes.append(
        {
            "content" : i.page_content,
            "type" : "text",
            "description" : llm.invoke(description_prompt + "\n" + i.page_content).content,
            "name" : llm.invoke(name_prompt + "\n" + i.page_content).content
        }
    )

with open('epsiodes.json', 'w') as f:
    json.dump(epsiodes, f)

