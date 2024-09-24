from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.connection import get_db, engine
from src.models import Base, Ticket

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# Pydantic models for request body
class TicketCreate(BaseModel):
    title: str
    description: str

class TicketUpdateStatus(BaseModel):
    status: str

# Helper function to convert SQLAlchemy object to dict
def ticket_to_dict(ticket: Ticket):
    return {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status
    }

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/tickets/", response_model=dict)
async def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    new_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        status="todo"  # Default status
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return {"message": "Ticket created successfully", "ticket": ticket_to_dict(new_ticket)}

@app.get("/tickets/")
async def get_tickets(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    tickets = db.query(Ticket).offset(skip).limit(limit).all()
    return {"tickets": [ticket_to_dict(ticket) for ticket in tickets]}

@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"ticket": ticket_to_dict(ticket)}

@app.put("/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: int, ticket_update: TicketUpdateStatus, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = ticket_update.status
    db.commit()
    db.refresh(ticket)
    return {"message": "Ticket status updated", "ticket": ticket_to_dict(ticket)}
