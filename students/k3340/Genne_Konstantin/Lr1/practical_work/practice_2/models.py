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