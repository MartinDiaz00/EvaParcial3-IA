from fastapi import FastAPI
from pydantic import BaseModel
from .agent import HealthTechAgent

app = FastAPI(title='HealthTech EP3 Observabilidad')
agent = HealthTechAgent()

class QuestionRequest(BaseModel):
    question: str

@app.get('/')
def root():
    return {'message': 'HealthTech EP3 Observabilidad funcionando'}

@app.post('/agent/query')
def query_agent(request: QuestionRequest):
    result = agent.run(request.question)
    return result.__dict__
