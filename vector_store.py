from langchain_community.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain_core.tools import create_retriever_tool


embeddings = OpenAIEmbeddings(model='text-embedding-3-small', chunk_size=1)
vector_store = FAISS.load_local("faiss_index", embeddings)

retreiver = vector_store.as_retriever(search_kwargs={"k": 3}) # tells us give me the top 3 answers

# use this as a tool for the agent to retrieve relevant information from the vector store based on a query
retreiver_tool = create_retriever_tool(retriever=retreiver, name="vector_store_retriever", description="Useful for retrieving relevant information from the vector store based on a query. Input should be a string query, and output will be a list of relevant documents.")