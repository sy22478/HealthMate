from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict
import spacy

class VectorStore:
    def __init__(self, api_key: str, environment: str, index_name: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)
        self.embeddings = OpenAIEmbeddings()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            self.nlp = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

    def spacy_chunk(self, text: str) -> list:
        if not self.nlp:
            return self.text_splitter.split_text(text)
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        chunks = []
        current_chunk = ""
        current_size = 0
        i = 0
        while i < len(sentences):
            while i < len(sentences) and current_size + len(sentences[i]) <= self.chunk_size:
                current_chunk += sentences[i] + " "
                current_size += len(sentences[i])
                i += 1
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Overlap: go back by enough sentences to cover the overlap
            overlap_size = 0
            j = i - 1
            overlap_chunk = ""
            while j >= 0 and overlap_size < self.chunk_overlap:
                overlap_chunk = sentences[j] + " " + overlap_chunk
                overlap_size += len(sentences[j])
                j -= 1
            current_chunk = overlap_chunk
            current_size = len(current_chunk)
        return chunks

    def add_documents(self, documents: List[Dict]):
        """Add medical documents to vector store"""
        for doc in documents:
            # Use spaCy-based chunking if possible
            chunks = self.spacy_chunk(doc['content'])
            for i, chunk in enumerate(chunks):
                vector = self.embeddings.embed_query(chunk)
                self.index.upsert([(
                    f"{doc['source']}_{i}",
                    vector,
                    {"text": chunk, "source": doc['source'], "title": doc['title']}
                )])

    def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar medical content"""
        query_vector = self.embeddings.embed_query(query)
        results = self.index.query(
            vector=query_vector,
            top_k=k,
            include_metadata=True
        )
        return [
            {
                "text": match.metadata["text"],
                "source": match.metadata["source"],
                "score": match.score
            }
            for match in results.matches
        ] 