
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

API_KEY = os.environ.get("GOOGLE_API_KEY")
DB_URL = os.environ.get("NEON_DB")
# print(f"DB: {DB_URL}")

# DB_URL = "postgresql://neondb_owner:npg_jH1SvZmUphN4@ep-small-frost-a4maf7mh-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

if not API_KEY:
    print("⚠️  WARNING: GEMINI_API_KEY not found. Please export it.")

app = FastAPI(title="Stateless SQL Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    engine = create_engine(DB_URL)
    db = SQLDatabase(engine)
    print("✅ Database Connected")
except Exception as e:
    print(f"❌ Database Connection Failed: {e}")
    exit(1)


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-09-2025",
    temperature=0,
    google_api_key=API_KEY
)

system_prefix = """You are an expert SQL Data Analyst.
Given an input question, create a syntactically correct PostgreSQL query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.
You have access to tools for interacting with the database.
Only use the below tools. Only use the information returned by the below tools to construct your final answer.
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

To start you should ALWAYS look at the tables in the database to see what you can query.
Do NOT skip this step.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prefix),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    prompt=prompt,
    agent_type="tool-calling",
    verbose=True,
    agent_executor_kwargs={"return_intermediate_steps": True} 
)


class ChatRequest(BaseModel):
    query: str

@app.post("/analyze")
async def chat(request: ChatRequest):
    try:
        response = agent_executor.invoke({"input": request.query})
        
        intermediate_steps = response.get("intermediate_steps", [])
        
        last_sql_query = None
        last_sql_result = None
        
        for action, observation in intermediate_steps:
            if action.tool == "sql_db_query":
                last_sql_query = action.tool_input
                last_sql_result = str(observation)

        result = {
            "response": response["output"],
            "sql_query": last_sql_query,
            "sql_data": last_sql_result
        }
        print(f"\n\n\nResult: \n{result}")
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
