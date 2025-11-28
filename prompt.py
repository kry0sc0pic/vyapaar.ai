import psycopg2
from fastapi import FastAPI, HTTPException
from cachetools import TTLCache, cached
import time
from config.template import PROMPT_TEMPLATE

from questions.simple_questions import questions as simple

app = FastAPI()

report_cache = TTLCache(maxsize=1, ttl=60*30)

DB_CONFIG = {
    "dbname": "kirana_inventory",
    "user": "admin",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

app = FastAPI()

report_items = simple 

@cached(report_cache)
def generate_report():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print(f"No. of items: {len(report_items)}")

        prompt_context = ""
        
        for idx, item in enumerate(report_items):
            # print(f"Processing: {idx}")
            
            cur.execute(item['sql'])
            result = cur.fetchone()
            raw_value = result[0] if result else None

            formatted_value = ""
            
            if item['format_type'] == 'currency':
                val_float = float(raw_value) if raw_value else 0.0
                formatted_value = f"₹ {val_float:,.2f}"
            else:
                formatted_value = str(raw_value) if raw_value else "None"

            answer_text = item['template'].format(value=formatted_value)
            
            q = f"Question: {item['question']}"
            ans = f"Answer: {answer_text}"

            prompt_context += f"\n{q}\n{ans}"

        cur.close()
        conn.close()

        return prompt_context

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if conn:
            conn.close()



@app.get("/prompt")
async def get_system_prompt():
    formatted_prompt = PROMPT_TEMPLATE.format(cached_questions=generate_report())
    return {
        "context": formatted_prompt
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
