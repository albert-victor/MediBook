"""Doctor portrait paths from static image pools (female / male)."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".webp", ".png"}
FEMALE_SUBDIR = "female_doctors"
EXCLUDED_SUBDIRS = {FEMALE_SUBDIR, "services"}

_pools: dict[str, list[str]] | None = None
_rank_index: dict[str, dict[int, int]] | None = None


def invalidate_doctor_image_cache() -> None:
    """Clear cached pools and gender rank maps (call after doctor roster changes)."""
    global _pools, _rank_index
    _pools = None
    _rank_index = None


def _images_root() -> Path:
    return Path(get_settings().static_dir) / "assets" / "images"


def _load_pools() -> dict[str, list[str]]:
    root = _images_root()
    female_dir = root / FEMALE_SUBDIR
    female = (
        sorted(
            p.name
            for p in female_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        )
        if female_dir.is_dir()
        else []
    )
    male = sorted(
        p.name
        for p in root.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )
    return {"female": female, "male": male}


def _pool_key(gender: str | None) -> str:
    return "female" if (gender or "").lower() == "female" else "male"


def _static_image_url(relative_path: str) -> str:
    encoded = "/".join(quote(part) for part in relative_path.split("/"))
    return f"/static/{encoded}"


def _url_for_pool_file(pool_key: str, filename: str) -> str:
    if pool_key == "female":
        return _static_image_url(f"assets/images/{FEMALE_SUBDIR}/{filename}")
    return _static_image_url(f"assets/images/{filename}")


def _ensure_pools() -> dict[str, list[str]]:
    global _pools
    if _pools is None:
        _pools = _load_pools()
    return _pools


def _build_rank_index(db: Session) -> dict[str, dict[int, int]]:
    """Map doctor id -> pool index, unique per gender when pool has enough images."""
    from app.models import Doctor

    pools = _ensure_pools()
    rank_index: dict[str, dict[int, int]] = {"female": {}, "male": {}}

    for gender in ("female", "male"):
        pool = pools.get(gender) or []
        if not pool:
            continue
        doctor_ids = list(
            db.scalars(
                select(Doctor.id).where(Doctor.gender == gender).order_by(Doctor.id)
            )
        )
        for i, doctor_id in enumerate(doctor_ids):
            rank_index[gender][doctor_id] = i % len(pool)

    return rank_index


def _ensure_rank_index() -> dict[str, dict[int, int]]:
    global _rank_index
    if _rank_index is not None:
        return _rank_index

    from app.database import SessionLocal

    with SessionLocal() as db:
        _rank_index = _build_rank_index(db)
    return _rank_index


def get_doctor_image_url(
    doctor_id: int,
    gender: str | None,
    avatar_url: str | None = None,
) -> str | None:
    """Return a portrait URL from the gender image pool, or the stored avatar."""
    if avatar_url:
        return avatar_url

    pools = _ensure_pools()
    pool_key = _pool_key(gender)
    pool = pools.get(pool_key) or []
    if not pool:
        pool = pools.get("male" if pool_key == "female" else "female") or []
        pool_key = "male" if pool_key == "female" else "female"
    if not pool:
        return None

    rank_map = _ensure_rank_index()
    pool_index = rank_map.get(pool_key, {}).get(doctor_id)
    if pool_index is None:
        pool_index = (doctor_id * 2654435761) % len(pool)

    filename = pool[pool_index]
    return _url_for_pool_file(pool_key, filename)


def assign_doctor_portraits(db: Session) -> int:
    """Persist one unique portrait per doctor (by gender order). Returns rows updated."""
    from app.models import Doctor

    pools = _ensure_pools()
    updated = 0

    for gender in ("female", "male"):
        pool = pools.get(gender) or []
        if not pool:
            continue
        doctors = list(
            db.scalars(
                select(Doctor).where(Doctor.gender == gender).order_by(Doctor.id)
            )
        )
        for i, doctor in enumerate(doctors):
            url = _url_for_pool_file(gender, pool[i % len(pool)])
            if doctor.avatar_url != url:
                doctor.avatar_url = url
                updated += 1

    if updated:
        db.commit()
        invalidate_doctor_image_cache()

    return updated
