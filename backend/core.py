from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain.chains.retrieval import create_retrieval_chain
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

INDEX_NAME = "langchain-docs-2025"


def run_llm(query: str, chat_history: List[Dict[str, Any]] = [], verbose: bool = False):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    docsearch = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    chat = ChatOpenAI(verbose=False, temperature=0)

    # Create a contextualized query that includes recent chat history for better coreference resolution
    contextualized_query = query
    if chat_history:
        # Get the last few exchanges for context
        recent_context = []
        for msg in chat_history[-6:]:  # Last 3 exchanges (user + assistant pairs)
            if msg["role"] == "user":
                recent_context.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                recent_context.append(f"Assistant: {msg['content'][:200]}...")  # Truncate long responses
        
        if recent_context:
            context_str = "\n".join(recent_context)
            contextualized_query = f"""Given this recent conversation:
{context_str}

Current question: {query}

Please search for information relevant to the current question, taking into account the conversation context for any references like 'it', 'that', 'they', 'the company', etc."""

    # Test the retriever to see what documents it finds
    retriever = docsearch.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )
    docs = retriever.invoke(contextualized_query)
    
    if verbose:
        print(f"🔍 Found {len(docs)} relevant documents from Pinecone")
        print(f"📝 Contextualized query: {contextualized_query[:200]}...")
        
        # Print details about all retrieved documents
        for i, doc in enumerate(docs):
            print(f"📄 Document {i+1}:")
            print(f"   Source: {doc.metadata.get('source', 'unknown')}")
            print(f"   Domain: {doc.metadata.get('domain', 'unknown')}")
            print(f"   Title: {doc.metadata.get('title', 'unknown')}")
            print(f"   Content preview: {doc.page_content[:200]}...")
            print()

    # Create a conversational retrieval chain that includes chat history
    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    stuff_documents_chain = create_stuff_documents_chain(chat, retrieval_qa_chat_prompt)

    qa = create_retrieval_chain(
        retriever=retriever, combine_docs_chain=stuff_documents_chain
    )
    
    # Include chat history in the context for the LLM
    result = qa.invoke({
        "input": query,
        "chat_history": chat_history
    })
    
    return result

if __name__ == "__main__":
    # Example usage - replace with your own query
    query = "Is Thrive TRM SOC 2 compliant?"
    res = run_llm(query, verbose=True)  # Enable verbose for command line usage
    print(f"\nANSWER: {res['answer']}")