from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Field, create_engine,Session,select 
import settings
from typing import Annotated
from contextlib import asynccontextmanager #will create context for app that how to run the app

# Step-1: Create Database on Neon
# Step-2: Create .env file for environment variables
# Step-3: Create setting.py file for encrypting DatabaseURL
# Step-4: Create a Model
# Step-5: Create Engine
# Step-6: Create function for table creation
# Step-7: Create function for session management
# Step-8: Create contex manager for app lifespan
# Step-9: Create all endpoints of todo app


#create model
    #data model
    #table model

class Todo (SQLModel, table=True): #can use for table creation and data validation after using table attribute for table creation 
    id: int | None = Field(default=None, primary_key=True) # int incase of search or update or delete and None when create Todo
    content : str = Field(index=True, min_length=3,max_length=54) #index=True will index in database whe we search for todo then whole table will not be scanned 
    is_completed :bool = Field(default=False) 


#engine is one for whole app
connection_string : str = str(settings.DATABASE_URL).replace("postgresql","postgresql+psycopg") #ti add psycopg in database url
engine = create_engine(connection_string, connect_args={"sslmode":"require"}, pool_recycle=300, pool_size=10, echo=True)  #driver for converting orm commands to sql commands to understand by db psycopy[binary], sslmode for sequre connection
#pool recycle for termination of connection , echo is used for stepwise working in terminal

def create_tables():
    SQLModel.metadata.create_all(engine) #to create table in database by using engine

# todo1 : Todo = Todo(content="first task")
# todo2 : Todo = Todo(content=" 2nd task")

# #session: seperate session for each functionality/transaction
# session = Session(engine)

# #create todos in database

# session.add(todo1)
# session.add(todo2)
# print(f'Before Commit {todo1}')
# session.commit()
# session.refresh(todo1)
# print(f'After Commit {todo1}')
# session.close()



def get_session():
    with Session(engine) as session:
        yield session


@asynccontextmanager #this will run before the app starts to ensure stability
async def lifespan(app:FastAPI):
    print('creating tables')
    create_tables()
    print('table created')
    yield







app = FastAPI(lifespan=lifespan, title="Todo App Multi", version='1.0.0')

@app.get("/")
async def root():
    return {"message": "Welcome to todo app"}

@app.post('/todos/', response_model=Todo)
async def create_todo(todo: Todo, session:Annotated[Session,Depends(get_session)]):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.get('/todos/', response_model=list[Todo])
async def get_all(session:Annotated[Session,Depends(get_session)]):
    statement = select(Todo)
    todos = session.exec(statement).all()
    if todos:
        return todos
    else:
        raise HTTPException(status_code=404, detail="Not Found")
    # session.exec(select(Todo)).all()


@app.get('/todos/{id}', response_model=Todo)
async def get_single_todo(id: int, session:Annotated[Session,Depends(get_session)]):
    todo = session.exec(select(Todo).where(Todo.id==id)).first() 
    if todo:
        return todo
    else:
        raise HTTPException(status_code=404, detail="Not Found")

@app.put('/todos/{id}')
async def edit_todo(id: int,todo: Todo, session:Annotated[Session,Depends(get_session)]):
    existing_todo = session.exec(select(Todo).where(Todo.id == id)).first()
    #existing_todo = session.get(Todo,id)
    if existing_todo:
        existing_todo.content = todo.content
        existing_todo.is_completed = todo.is_completed
        session.add(existing_todo)
        session.commit()
        session.refresh(existing_todo)
        return existing_todo
    else:
        raise HTTPException(status_code=404, detail="No task found")

@app.delete('/todos/{id}')
async def delete_todo(id:int, session:Annotated[Session,Depends(get_session)]):
    #todo = session.exec(select(Todo).where(Todo.id==id)).first() #this gives error so we change it to get method
    todo = session.get(Todo,id)
    if todo:
        session.delete(todo)
        session.commit()
        # session.refresh(todo)
        return{"messege":"successfully deleted"}
    else:
        raise HTTPException(status_code=404, detail="Not Found")