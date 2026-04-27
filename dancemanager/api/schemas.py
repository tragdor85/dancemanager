"""Pydantic schemas for API request/response models."""

__all__ = [
    "make_dancer_id",
    "make_team_id",
    "make_class_id",
    "make_instructor_id",
    "make_dance_id",
    "make_recital_id",
    "make_studio_id",
]

from pydantic import BaseModel, Field
from typing import Optional, List
from dancemanager.models import (  # noqa: F401
    make_dancer_id,
    make_team_id,
    make_class_id,
    make_instructor_id,
    make_dance_id,
    make_recital_id,
    make_studio_id,
)


# Dancer schemas
class DancerCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Dancer name")
    team_id: Optional[str] = None
    notes: str = Field(default="", description="Optional notes")


class DancerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="Dancer name")
    team_id: Optional[str] = Field(default=None, description="Team ID")
    notes: Optional[str] = Field(default=None, description="Notes")


class DancerResponse(BaseModel):
    id: str
    name: str
    team_id: Optional[str] = None
    class_ids: List[str] = []
    notes: str = ""


# Team schemas
class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Team name")
    dancer_ids: List[str] = Field(default=[], description="Dancer IDs")
    notes: str = Field(default="", description="Optional notes")


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="Team name")
    notes: Optional[str] = Field(default=None, description="Notes")


class TeamResponse(BaseModel):
    id: str
    name: str
    dancer_ids: List[str] = []
    class_ids: List[str] = []
    notes: str = ""


# Class schemas
class ClassCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Class name")
    instructor_id: Optional[str] = None
    notes: str = Field(default="", description="Optional notes")


class ClassUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="Class name")
    instructor_id: Optional[str] = Field(default=None, description="Instructor ID")
    notes: Optional[str] = Field(default=None, description="Notes")


class ClassResponse(BaseModel):
    id: str
    name: str
    instructor_id: Optional[str] = None
    team_ids: List[str] = []
    dancer_ids: List[str] = []
    notes: str = ""


# Instructor schemas
class InstructorCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Instructor name")
    notes: str = Field(default="", description="Optional notes")


class InstructorUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="Instructor name")
    notes: Optional[str] = Field(default=None, description="Notes")


class InstructorResponse(BaseModel):
    id: str
    name: str
    class_ids: List[str] = []
    dance_ids: List[str] = []
    notes: str = ""


# Dance schemas
class DanceCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Dance name")
    song_name: str = Field(..., min_length=1, description="Song name")
    instructor_id: Optional[str] = None
    dancer_ids: List[str] = Field(default=[], description="Individual dancer IDs")
    team_ids: List[str] = Field(
        default=[], description="Team IDs whose members are included"
    )
    notes: str = Field(default="", description="Optional notes")


class DanceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="Dance name")
    song_name: Optional[str] = Field(default=None, description="Song name")
    instructor_id: Optional[str] = Field(default=None, description="Instructor ID")
    dancer_ids: Optional[List[str]] = Field(
        default=None, description="Individual dancer IDs"
    )
    team_ids: Optional[List[str]] = Field(default=None, description="Team IDs")
    notes: Optional[str] = Field(default=None, description="Notes")


class DanceResponse(BaseModel):
    id: str
    name: str
    song_name: str
    instructor_id: Optional[str] = None
    dancer_ids: List[str] = []
    team_ids: List[str] = []
    notes: str = ""


# Recital schemas
class RecitalCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Recital name")
    date: Optional[str] = None
    venue: Optional[str] = None
    notes: str = Field(default="", description="Optional notes")


class RecitalUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="Recital name")
    date: Optional[str] = None
    venue: Optional[str] = None
    notes: Optional[str] = Field(default=None, description="Notes")


class DanceSlot(BaseModel):
    dance_id: str
    position: int


class RecitalResponse(BaseModel):
    id: str
    name: str
    date: Optional[str] = None
    venue: Optional[str] = None
    dance_ids: List[str] = []
    notes: str = ""


class ScheduleSlot(BaseModel):
    position: int
    dance_id: str
    song_name: str
    dancers: List[str] = []
    notes: str = ""


# Studio schemas
class StudioCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Studio name")
    location: Optional[str] = None
    capacity: int = Field(default=20, ge=1, description="Maximum dancer capacity")
    equipment: List[str] = Field(default=[], description="List of equipment items")


class StudioUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="Studio name")
    location: Optional[str] = Field(default=None, description="Location/address")
    capacity: Optional[int] = Field(
        default=None, ge=1, description="Maximum dancer capacity"
    )
    equipment: Optional[List[str]] = Field(
        default=None, description="List of equipment items"
    )


class StudioResponse(BaseModel):
    id: str
    name: str
    location: Optional[str] = None
    capacity: int = 20
    schedule: List[dict] = []
    notes: str = ""
