from fastapi import FastAPI

from typing import List
from typing_extensions import TypedDict

from models import Warrior, Profession, ProfessionCreate, ProfessionUpdate

app = FastAPI()

temp_bd = [
{
    "id": 1,
    "race": "director",
    "name": "Мартынов Дмитрий",
    "level": 12,
    "profession": {
        "id": 1,
        "title": "Влиятельный человек",
        "description": "Эксперт по всем вопросам"
    },
    "skills":
        [{
            "id": 1,
            "name": "Купле-продажа компрессоров",
            "description": ""

        },
        {
            "id": 2,
            "name": "Оценка имущества",
            "description": ""

        }]
},
{
    "id": 2,
    "race": "worker",
    "name": "Андрей Косякин",
    "level": 12,
    "profession": {
        "id": 1,
        "title": "Дельфист-гребец",
        "description": "Уважаемый сотрудник"
    },
    "skills": []
},
]

temp_professions = [
    {"id": 1, "title": "Влиятельный человек", "description": "Эксперт по всем вопросам"},
    {"id": 2, "title": "Дельфист-гребец", "description": "Уважаемый сотрудник"}
]

@app.get('/')
def hello():
    return "Hello, [username]!"

@app.get("/warriors_list")
def warriors_list() -> List[Warrior]:
    return temp_bd


@app.get("/warrior/{warrior_id}")
def warriors_get(warrior_id: int) -> List[Warrior]:
    return [warrior for warrior in temp_bd if warrior.get("id") == warrior_id]


@app.post("/warrior")
def warriors_create(warrior: Warrior) -> TypedDict('Response', {"status": int, "data": Warrior}):
    warrior_to_append = warrior.model_dump()
    temp_bd.append(warrior_to_append)
    return {"status": 200, "data": warrior}


@app.delete("/warrior/delete{warrior_id}")
def warrior_delete(warrior_id: int):
    for i, warrior in enumerate(temp_bd):
        if warrior.get("id") == warrior_id:
            temp_bd.pop(i)
            break
    return {"status": 201, "message": "deleted"}


@app.put("/warrior{warrior_id}")
def warrior_update(warrior_id: int, warrior: Warrior) -> List[Warrior]:
    for war in temp_bd:
        if war.get("id") == warrior_id:
            warrior_to_append = warrior.model_dump()
            temp_bd.remove(war)
            temp_bd.append(warrior_to_append)
    return temp_bd


@app.get("/profession_list")
def get_professions() -> List[Profession]:
    return temp_professions

@app.get("/profession/{profession_id}")
def get_profession(profession_id: int) -> List[Profession]:
    return [profession for profession in temp_professions if profession.get("id") == profession_id]

@app.post("/profession")
def create_profession(profession: ProfessionCreate) -> TypedDict('Response', {"status": int, "data": Warrior}):
    new_id = max((p["id"] for p in temp_professions), default=0) + 1
    new_prof = {"id": new_id, **profession.model_dump()}
    temp_professions.append(new_prof)
    return {"status": 200, "data": new_prof}

@app.patch("/profession/{profession_id}")
def update_profession(profession_id: int, profession_update: ProfessionUpdate) -> Profession:
    for p in temp_professions:
        if p["id"] == profession_id:
            if profession_update.title is not None:
                p["title"] = profession_update.title
            if profession_update.description is not None:
                p["description"] = profession_update.description
            return p

@app.delete("/profession/{profession_id}")
def delete_profession(profession_id: int):
    for i, p in enumerate(temp_professions):
        if p["id"] == profession_id:
            temp_professions.pop(i)
            return {"status": 201, "message": "deleted"}