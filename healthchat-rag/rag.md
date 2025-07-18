2. Improved Chunking
Adjust chunk size and overlap for your vector store to balance context relevance and completeness.
Optionally, use sentence or paragraph boundaries for chunking instead of fixed-size chunks.
3. Source Ranking/Filtering
Optionally, prioritize or filter context by source credibility or recency.
Default Implementation Plan
Enhance get_relevant_context in MedicalKnowledgeBase to:
Expand the query using synonyms and user profile.
(Optionally) Add a simple ranking by source if multiple results are returned.
3. Add User Feedback on Context Quality
Allow users to rate the helpfulness or accuracy of the context used in responses.
Store feedback for future model improvements or admin review.
Recommended Next Steps (Default Path):
Add more sources to MedicalKnowledgeBase.
Improve the get_relevant_context method for better query expansion.
Add a feedback mechanism in the frontend and backend.
4. Using a better embedding model:
Embedding models can impact the quality and accuracy of your search results
Test embedding models on sample data since MTEB leaderboard is easy to game
Consider domain-specific models: Voyage has models for code, finance, law
5. Reranking:
Send similarity results to reranking models (trained to calculate relevancy).
Rerank models: Take query and related document (chunks), generate relevancy score for each document, and return results ranked by relevance, hence reranks
Filter out irrelevant results: Don’t confuse LLM with irrelevant (or contradictory) data
6. Query rewriting
Users write bad retrieval queries
7. Reasoning model
Use models that can trace thinking
Open source models with thinking
8. Use metadata filtering
Attach metadata to chunks:
Source metadata
Static, user defined metadata
Inferred metadata (ex from file path)
Extracted metadata
Filtering on retrieval
Narrows down semantic search to only chunks that match the filter
Can combine with application features/widgets (ex only documents about NVIDIA)
Powerful for agentic RAG
Agents can calculate the filters
Can be combined with remote MCP
9. Metadata enrichment
Add metadata to chunk
Before calculating vector 
Before writing to vector DB
Docs with many chunks
First chunk contains important information, extract, add to each chunk
Add summary of document to each chunk
Contextual retrieval from Anthropic
10. Knowledge graph metadata
Knowledge graph is a type of metadata
Shows relationships (works for, member of, is a) between entities (people, companies, things)
Important for some data types (ex email messages)
Graph databases (ex Neo4J) make writing and querying relationships easy
Hard part is determining relationship tuples in the data (entity 1, relationship, entity 2)
Automatically by models (ex Vectorize Iris)
When using model-based extraction, must deduplicate (works for vs employed by, Chris Bartholomew vs Christopher Bartholomew)
Use semantic similarity to deduplicate
Two stage retrieval
Find semantically similar chunks with knowledge graph metadata attached. 
Query graph database for related chunks by relationship
Send all chunks to LLM
