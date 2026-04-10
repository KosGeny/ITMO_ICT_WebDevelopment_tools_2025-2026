# Практика 1.2. Настройка БД, SQLModel и миграции через Alembic

В ходе практики была подключена база данных PostgreSQL, изменены и дополнены модели для работы с БД, добавлены новые эндпоинты.

## connection.py
```python
from sqlmodel import SQLModel, Session, create_engine

db_url = 'postgresql://postgres:123@localhost/warriors_db'
engine = create_engine(db_url, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
```  

## main.py
```python
from fastapi import FastAPI

from typing import List
from typing_extensions import TypedDict

from models import Warrior, WarriorDefault, Profession, ProfessionDefault, WarriorProfessions, Skill, SkillDefault, WarriorFull, SkillWarriorLink

from connection import init_db, get_session

from fastapi import Depends, HTTPException
from sqlmodel import select

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/warrior")
def warriors_create(warrior: WarriorDefault, session=Depends(get_session)) -> TypedDict('Response', {"status": int,
                                                                                                     "data": Warrior}):
    warrior = Warrior.model_validate(warrior)
    session.add(warrior)
    session.commit()
    session.refresh(warrior)
    return {"status": 200, "data": warrior}

@app.get("/warriors_list")
def warriors_list(session=Depends(get_session)) -> List[Warrior]:
    return session.exec(select(Warrior)).all()

@app.patch("/warrior{warrior_id}")
def warrior_update(warrior_id: int, warrior: WarriorDefault, session=Depends(get_session)) -> WarriorDefault:
    db_warrior = session.get(Warrior, warrior_id)
    if not db_warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")
    warrior_data = warrior.model_dump(exclude_unset=True)
    for key, value in warrior_data.items():
        setattr(db_warrior, key, value)
    session.add(db_warrior)
    session.commit()
    session.refresh(db_warrior)
    return db_warrior

@app.delete("/warrior/delete{warrior_id}")
def warrior_delete(warrior_id: int, session=Depends(get_session)):
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")
    session.delete(warrior)
    session.commit()
    return {"ok": True}

@app.get("/professions_list")
def professions_list(session=Depends(get_session)) -> List[Profession]:
    return session.exec(select(Profession)).all()


@app.get("/profession/{profession_id}")
def profession_get(profession_id: int, session=Depends(get_session)) -> Profession:
    return session.get(Profession, profession_id)


@app.post("/profession")
def profession_create(prof: ProfessionDefault, session=Depends(get_session)) -> TypedDict('Response', {"status": int,
                                                                                                     "data": Profession}):
    prof = Profession.model_validate(prof)
    session.add(prof)
    session.commit()
    session.refresh(prof)
    return {"status": 200, "data": prof}

@app.get("/skills_list")
def skills_list(session = Depends(get_session)) -> List[Skill]:
    return session.exec(select(Skill)).all()

@app.get("/skill/{skill_id}")
def skill_get(skill_id: int, session = Depends(get_session)) -> Skill:
    return session.get(Skill, skill_id)

@app.post("/skill")
def skill_create(skill: SkillDefault, session = Depends(get_session)) -> TypedDict('Response', {"status": int, "data": Skill}):
    db_skill = Skill.model_validate(skill)
    session.add(db_skill)
    session.commit()
    session.refresh(db_skill)
    return {"status": 200, "data": db_skill}

@app.get("/warrior/{warrior_id}", response_model=WarriorFull)
def warrior_get(warrior_id: int, session = Depends(get_session)) -> Warrior:
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")
    return warrior

@app.post("/warrior/{warrior_id}/skills/{skill_id}", status_code=201)
def assign_skill_to_warrior(
    warrior_id: int,
    skill_id: int,
    session = Depends(get_session)
):
    warrior = session.get(Warrior, warrior_id)
    skill = session.get(Skill, skill_id)
    
    if not warrior or not skill:
        raise HTTPException(status_code=404, detail="Warrior or Skill not found")
    
    existing_link = session.exec(
        select(SkillWarriorLink).where(
            SkillWarriorLink.warrior_id == warrior_id,
            SkillWarriorLink.skill_id == skill_id
        )
    ).first()
    
    if existing_link:
        raise HTTPException(status_code=400, detail="Skill already assigned to this warrior")
    
    link = SkillWarriorLink(warrior_id=warrior_id, skill_id=skill_id)
    session.add(link)
    session.commit()
    
    return {"status": "ok", "message": f"Skill {skill_id} assigned to warrior {warrior_id}"}
```

## models.py
```python
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class RaceType(Enum):
    director = "director"
    worker = "worker"
    junior = "junior"


class SkillWarriorLink(SQLModel, table=True):
    warrior_id: int = Field(foreign_key="warrior.id", primary_key=True)
    skill_id: int = Field(foreign_key="skill.id", primary_key=True)


class ProfessionDefault(SQLModel):
    title: str
    description: Optional[str] = None

class Profession(ProfessionDefault, table=True):
    id: int = Field(default=None, primary_key=True)
    warriors_prof: List["Warrior"] = Relationship(back_populates="profession")


class SkillDefault(SQLModel):
    name: str
    description: Optional[str] = None

class Skill(SkillDefault, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    warriors: List["Warrior"] = Relationship(
        back_populates="skills", 
        link_model=SkillWarriorLink
    )


class WarriorDefault(SQLModel):
    race: RaceType
    name: str
    level: int
    profession_id: Optional[int] = Field(default=None, foreign_key="profession.id")

class Warrior(WarriorDefault, table=True):
    id: int = Field(default=None, primary_key=True)
    profession: Optional[Profession] = Relationship(back_populates="warriors_prof")
    skills: List[Skill] = Relationship(
        back_populates="warriors", 
        link_model=SkillWarriorLink
    )


class WarriorProfessions(WarriorDefault):
    id: Optional[int] = None
    profession: Optional[Profession] = None

class WarriorSkills(WarriorDefault):
    id: Optional[int] = None
    skills: List[Skill] = []

class WarriorFull(WarriorDefault):
    id: Optional[int] = None
    profession: Optional[Profession] = None
    skills: List[Skill] = []
```