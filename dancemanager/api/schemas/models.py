from dancemanager.models import DEFAULT_STORE_SCHEMA
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class Instructor(BaseModel):
    id: str = Field(default_factory=lambda: "instructor")
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class Dancer(BaseModel):
    id: str = Field(default_factory=lambda: "dancer")
    name: str
    age: Optional[int] = None
    level: Optional[str] = None
    teams: List[str] = []


class Team(BaseModel):
    id: str = Field(default_factory=lambda: "team")
    name: str
    dancers: List[str] = []


class Class(BaseModel):
    id: str = Field(default_factory=lambda: "class")
    name: str
    instructor_id: Optional[str] = None
    days: List[str] = []
    times: List[str] = []


class Dance(BaseModel):
    id: str = Field(default_factory=lambda: "dance")
    name: str
    level: Optional[str] = None
    difficulty: Optional[int] = None


class Recital(BaseModel):
    id: str = Field(default_factory=lambda: "recital")
    name: str
    date: Optional[date] = None
    dances: List[str] = []
    instructors: List[str] = []
