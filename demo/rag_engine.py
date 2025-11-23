"""
RAG Engine for Legal Assistant Demo
Handles document loading, embedding, vector search, and LLM response generation
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple
import hashlib

# Vector DB and Embeddings
import chromadb
from chromadb.utils import embedding_functions

# LLM Integration (supports both OpenAI and Anthropic)
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class LegalRAGEngine:
    """RAG Engine specialized for Hungarian legal documents"""

    def __init__(
        self,
        laws_dir: str = "data/laws",
        chroma_persist_dir: str = "data/chroma_db",
        llm_provider: str = "openai",  # "openai" or "anthropic"
        api_key: str = None
    ):
        """
        Initialize RAG Engine

        Args:
            laws_dir: Directory containing law markdown files
            chroma_persist_dir: Directory for ChromaDB persistence
            llm_provider: "openai" or "anthropic"
            api_key: API key for the LLM provider
        """
        self.laws_dir = Path(laws_dir)
        self.chroma_persist_dir = Path(chroma_persist_dir)
        self.llm_provider = llm_provider
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_persist_dir))

        # Use sentence-transformers for multilingual embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="hungarian_laws",
            embedding_function=self.embedding_function,
            metadata={"description": "Hungarian legal documents"}
        )

        # Law metadata cache
        self.law_metadata = self._load_law_metadata()

        # Configure LLM client
        if self.llm_provider == "openai" and HAS_OPENAI:
            openai.api_key = self.api_key
            self.llm_model = "gpt-4"
        elif self.llm_provider == "anthropic" and HAS_ANTHROPIC:
            self.anthropic_client = anthropic.Anthropic(api_key=self.api_key)
            self.llm_model = "claude-3-haiku-20240307"
        else:
            raise ValueError(f"LLM provider {llm_provider} not supported or library not installed")

    def _load_law_metadata(self) -> Dict[str, Dict]:
        """Load metadata about available laws"""
        metadata = {}
        law_mapping = {
            "alaptörvény.md": {
                "title": "Magyarország Alaptörvénye",
                "code": "Alaptörvény",
                "year": 2011,
                "category": "alkotmányjog"
            },
            "BTK_clean.md": {
                "title": "Büntető Törvénykönyv",
                "code": "2012. évi C. törvény",
                "year": 2012,
                "category": "büntetőjog"
            },
            "Ptk_clean.md": {
                "title": "Polgári Törvénykönyv",
                "code": "2013. évi V. törvény",
                "year": 2013,
                "category": "polgári jog"
            },
            "Be_clean.md": {
                "title": "Büntetőeljárási törvény",
                "code": "2017. évi XC. törvény",
                "year": 2017,
                "category": "eljárásjog"
            },
            "Rtv_clean.md": {
                "title": "Rendőrségi törvény",
                "code": "1994. évi XXXIV. törvény",
                "year": 1994,
                "category": "rendészet"
            },
            "Fgy_tv_clean.md": {
                "title": "Fogyasztóvédelmi törvény",
                "code": "1997. évi CLV. törvény",
                "year": 1997,
                "category": "fogyasztóvédelem"
            }
        }
        return law_mapping

    def _chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Input text
            chunk_size: Target chunk size in characters
            overlap: Overlap size between chunks

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size

            # Try to break at paragraph boundary
            if end < text_len:
                # Look for paragraph break (double newline)
                para_break = text.rfind('\n\n', start, end)
                if para_break != -1 and para_break > start + chunk_size // 2:
                    end = para_break
                else:
                    # Look for single newline
                    line_break = text.rfind('\n', start, end)
                    if line_break != -1 and line_break > start + chunk_size // 2:
                        end = line_break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap

        return chunks

    def _extract_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Extract YAML frontmatter from markdown"""
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)

        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            content_without_frontmatter = content[frontmatter_match.end():]

            # Parse simple YAML (key: value format)
            frontmatter = {}
            for line in frontmatter_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()

            return frontmatter, content_without_frontmatter

        return {}, content

    def load_and_index_laws(self, force_reload: bool = False):
        """
        Load all law markdown files and index them in ChromaDB

        Args:
            force_reload: If True, clear existing collection and reload all
        """
        print(f"Loading laws from {self.laws_dir}...")

        # Check if collection already has documents
        if not force_reload and self.collection.count() > 0:
            print(f"Collection already has {self.collection.count()} documents. Skipping reload.")
            print("Use force_reload=True to re-index.")
            return

        if force_reload:
            # Clear collection
            self.chroma_client.delete_collection("hungarian_laws")
            self.collection = self.chroma_client.create_collection(
                name="hungarian_laws",
                embedding_function=self.embedding_function
            )

        total_chunks = 0

        for law_file, metadata in self.law_metadata.items():
            law_path = self.laws_dir / law_file

            if not law_path.exists():
                print(f"Warning: {law_file} not found. Skipping.")
                continue

            print(f"Processing {metadata['title']}...")

            # Read file
            with open(law_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract frontmatter
            frontmatter, content_clean = self._extract_frontmatter(content)

            # Chunk the text
            chunks = self._chunk_text(content_clean)
            print(f"  Created {len(chunks)} chunks")

            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []

            for i, chunk in enumerate(chunks):
                # Create unique ID using content hash
                chunk_id = hashlib.md5(f"{law_file}_{i}_{chunk[:100]}".encode()).hexdigest()
                ids.append(chunk_id)
                documents.append(chunk)

                chunk_metadata = {
                    "source_file": law_file,
                    "law_title": metadata['title'],
                    "law_code": metadata['code'],
                    "law_category": metadata['category'],
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                metadatas.append(chunk_metadata)

            # Add to collection in batches (ChromaDB has batch size limits)
            batch_size = 100
            for j in range(0, len(ids), batch_size):
                batch_ids = ids[j:j+batch_size]
                batch_docs = documents[j:j+batch_size]
                batch_meta = metadatas[j:j+batch_size]

                self.collection.add(
                    ids=batch_ids,
                    documents=batch_docs,
                    metadatas=batch_meta
                )

            total_chunks += len(chunks)

        print(f"\nIndexing complete! Total chunks: {total_chunks}")
        print(f"Collection size: {self.collection.count()}")

    def search_laws(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for relevant law sections

        Args:
            query: User query
            n_results: Number of results to return

        Returns:
            List of relevant law chunks with metadata
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "document": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })

        return formatted_results

    def generate_response(self, query: str, context_chunks: List[Dict]) -> str:
        """
        Generate AI response using LLM with retrieved context

        Args:
            query: User query
            context_chunks: Retrieved law chunks

        Returns:
            AI-generated response
        """
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            meta = chunk['metadata']
            context_parts.append(
                f"[Forrás {i}: {meta['law_title']} ({meta['law_code']})]\n{chunk['document']}"
            )

        context = "\n\n---\n\n".join(context_parts)

        # Construct prompt
        system_prompt = """Te egy magyar jogi asszisztens mesterséges intelligencia vagy.
Feladatod: Válaszolj a felhasználó jogi kérdésére a mellékelt törvényrészletek alapján.

FONTOS SZABÁLYOK:
1. Csak a mellékelt törvényrészleteket használd forrásként
2. Mindig hivatkozz a konkrét törvényre és paragrafusra
3. Ha nem vagy biztos, mondd meg
4. NE adj jogi tanácsot - csak tájékoztatást nyújts
5. Javasolj ügyvédi segítséget komplex esetekben
6. Írj érthetően, laikus felhasználók számára

Válasz formátum:
- Rövid összefoglaló (2-3 mondat)
- Releváns jogszabályi háttér (törvény citálás)
- Gyakorlati következmények
- Ajánlás következő lépésekre"""

        user_prompt = f"""Kérdés: {query}

Releváns törvényrészletek:

{context}

Kérlek, válaszolj a fenti kérdésre a törvényrészletek alapján!"""

        # Call LLM
        if self.llm_provider == "openai":
            response = openai.ChatCompletion.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content

        elif self.llm_provider == "anthropic":
            message = self.anthropic_client.messages.create(
                model=self.llm_model,
                max_tokens=1000,
                temperature=0.3,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return message.content[0].text

    def answer_query(self, query: str, n_results: int = 5) -> Dict:
        """
        Complete RAG pipeline: Search + Generate

        Args:
            query: User question
            n_results: Number of law chunks to retrieve

        Returns:
            Dict with answer, sources, and metadata
        """
        # Search for relevant law sections
        search_results = self.search_laws(query, n_results=n_results)

        # Generate response
        answer = self.generate_response(query, search_results)

        # Format sources
        sources = []
        for result in search_results:
            meta = result['metadata']
            sources.append({
                "law": meta['law_title'],
                "code": meta['law_code'],
                "category": meta['law_category']
            })

        # Detect legal category from query and sources
        detected_category = self._detect_legal_category(query, sources)

        return {
            "answer": answer,
            "sources": sources,
            "detected_category": detected_category,
            "query": query
        }

    def _detect_legal_category(self, query: str, sources: List[Dict]) -> str:
        """Detect legal category from query and sources"""
        query_lower = query.lower()

        # Keyword-based detection
        if any(word in query_lower for word in ['munka', 'felmondás', 'végkielégítés', 'munkaszerződés', 'fizetés', 'munkabér', 'túlóra']):
            return "munkajog"
        elif any(word in query_lower for word in ['fogyasztó', 'reklamáció', 'jótállás', 'garancia', 'vásárlás', 'termék']):
            return "fogyasztóvédelem"
        elif any(word in query_lower for word in ['válás', 'gyerek', 'tartás', 'házasság', 'család']):
            return "családjog"
        elif any(word in query_lower for word in ['ingatlan', 'lakás', 'ház', 'bérlés', 'adásvétel']):
            return "ingatlan"
        elif any(word in query_lower for word in ['bűn', 'büntető', 'büntetés', 'per', 'vádemel']):
            return "büntetőjog"

        # Fallback: use most common category from sources
        if sources:
            categories = [s['category'] for s in sources]
            return max(set(categories), key=categories.count)

        return "általános"


# Example usage
if __name__ == "__main__":
    # Initialize RAG Engine
    rag = LegalRAGEngine(
        laws_dir="data/laws",
        chroma_persist_dir="data/chroma_db",
        llm_provider="openai"  # or "anthropic"
    )

    # Load and index laws (first time only)
    rag.load_and_index_laws(force_reload=False)

    # Example query
    query = "Jogellenes a felmondásom? Nem kaptam végkielégítést."
    result = rag.answer_query(query)

    print("=" * 80)
    print(f"Kérdés: {result['query']}")
    print("=" * 80)
    print(f"\nVálasz:\n{result['answer']}")
    print(f"\nKategória: {result['detected_category']}")
    print(f"\nForrások:")
    for source in result['sources']:
        print(f"  - {source['law']} ({source['code']})")
