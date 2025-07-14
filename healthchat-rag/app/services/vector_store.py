from pinecone import Pinecone
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict

class VectorStore:
    def __init__(self, api_key: str, environment: str, index_name: str):
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def add_documents(self, documents: List[Dict]):
        """Add medical documents to vector store"""
        for doc in documents:
            chunks = self.text_splitter.split_text(doc['content'])
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