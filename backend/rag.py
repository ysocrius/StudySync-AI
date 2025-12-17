from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ingest import load_data
import os

class RAGSystem:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self.qa_chain = None
        self.full_lexical_context = ""
        # self.initialize_vector_store() # Removed to prevent blocking startup

    def initialize_vector_store(self, pdf_paths=None, video_urls=None, progress_callback=None):
        """Initializes or rebuilds the vector store from provided sources."""
        print("Initializing RAG System... (PDFs: {}, Videos: {})".format(pdf_paths, video_urls))
        if progress_callback:
            progress_callback("Initializing content ingestion...")
            
        raw_data = load_data(pdf_paths=pdf_paths, video_urls=video_urls, progress_callback=progress_callback)
        
        if not raw_data:
            print("No data found to index.")
            if progress_callback:
                progress_callback("No data found to index.")
            return

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        all_splits = []
        for item in raw_data:
            splits = text_splitter.create_documents(
                [item['text']], 
                metadatas=[{"source": item['source'], "type": item['type']}]
            )
            all_splits.extend(splits)

        if all_splits:
            # Store full text for summary/podcast generation (simple generic context)
            # Limit to ~100k chars to be safe with 4o-mini context window for now
            self.full_lexical_context = "\n\n".join([item['text'] for item in raw_data])[:100000]
            
            if progress_callback:
                progress_callback("Creating vector store index...")
            self.vector_store = FAISS.from_documents(all_splits, self.embeddings)
            
            if progress_callback:
                progress_callback("RAG System Ready!")
            
            # Setup QA Chain using modern LangChain API
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            
            # Custom Prompt
            template = """Use the following pieces of context to answer the question at the end. 
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            Use the style of a helpful tutor.
            
            Context: {context}
            
            Question: {question}
            
            Helpful Answer:"""
            
            prompt = ChatPromptTemplate.from_template(template)
            
            # Create retrieval chain using LCEL (LangChain Expression Language)
            retriever = self.vector_store.as_retriever(search_kwargs={"k": 6})
            
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)
            
            from langchain_core.runnables import RunnableParallel

            self.qa_chain = (
                RunnableParallel({"context": retriever | format_docs, "docs": retriever, "question": RunnablePassthrough()})
                .assign(answer=prompt | llm | StrOutputParser())
                .pick(["answer", "docs"])
            )
            
            print(f"RAG System Ready with {len(all_splits)} chunks.")
        else:
            print("No text chunks created.")

    def query(self, question):
        if not self.qa_chain:
            return {"answer": "System is not initialized or has no data.", "docs": []}
        
        return self.qa_chain.invoke(question)

    def stream_answer_with_docs(self, question):
        """Yields (chunk, None) for text, then (None, docs) at the end."""
        if not self.qa_chain:
            yield "System not initialized", None
            return

        retriever = self.vector_store.as_retriever(search_kwargs={"k": 6})
        docs = retriever.invoke(question)
        
        context_str = "\n\n".join(doc.page_content for doc in docs)
        
        template = """Use the following piece of context to answer the question.
        Context: {context}
        Question: {question}
        Helpful Answer:"""
        
        final_prompt = template.format(context=context_str, question=question)
        llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, streaming=True)
        
        for chunk in llm.stream(final_prompt):
             if chunk.content:
                 yield chunk.content, None
                 
        yield None, docs

    def get_summary(self):
        """Generates a summary of all content."""
        if not self.full_lexical_context and not self.vector_store:
            return "No content to summarize."
            
        # Use full context if available (better for comprehensive summary)
        if self.full_lexical_context:
            # We can use a direct LLM call here or just return the text for the caller to summarize
            # For this specific method which returns a string, let's ask LLM to summarize the full text
            # But wait, main.py uses this for the summary block on the left.
            # Let's verify we don't blow up the prompt. 100k chars is fine for 4o-mini.
            
            prompt = ChatPromptTemplate.from_template("Summarize the following content in a detailed and educational way:\n\n{context}")
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            chain = prompt | llm | StrOutputParser()
            try:
                return chain.invoke({"context": self.full_lexical_context[:50000]}) # Safe limit
            except:
                return self.query("Summarize main concepts")["answer"]
        
        return self.query("Provide a detailed summary of the main concepts discussed in the provided text and videos.")["answer"]

# Singleton instance for easy import
rag_system = RAGSystem()
