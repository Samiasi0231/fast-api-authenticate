
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_note_owner_or_admin
from app.models import Note, User
from app.schemas import NoteCreate, NoteResponse, NoteUpdate


router = APIRouter(prefix="/notes", tags=["Notes"])


@router.post(
    "/",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    note_data: NoteCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    new_note = Note(
        title=note_data.title,
        content=note_data.content,
        owner=current_user.username,
        is_public=note_data.is_public,
        tags=note_data.tags,
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return new_note


@router.get("/", response_model=list[NoteResponse])
def get_notes(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    tag: str | None = Query(default=None),
    search_term: str | None = Query(default=None),
):
    query = db.query(Note)

    if current_user.role != "admin":
        query = query.filter(
            (Note.owner == current_user.username)
            | (Note.is_public.is_(True))
        )

    if tag:
        query = query.filter(Note.tags.contains([tag]))

    if search_term:
        search_pattern = f"%{search_term}%"
        query = query.filter(
            (Note.title.ilike(search_pattern))
            | (Note.content.ilike(search_pattern))
        )

    return query.order_by(Note.created_at.desc()).all()


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    note = db.query(Note).filter(Note.id == note_id).first()

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    if (
        not note.is_public
        and note.owner != current_user.username
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this note",
        )

    return note


@router.put("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    note_data: NoteUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    note = db.query(Note).filter(Note.id == note_id).first()

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    get_note_owner_or_admin(note.owner, current_user)

    update_data = note_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(note, field, value)

    db.commit()
    db.refresh(note)

    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    note = db.query(Note).filter(Note.id == note_id).first()

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    get_note_owner_or_admin(note.owner, current_user)

    db.delete(note)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
