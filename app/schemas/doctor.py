"""Doctor directory API response schemas."""

from pydantic import BaseModel, Field


class DoctorReviewItem(BaseModel):
    id: int
    patient_name: str
    rating: int
    comment: str
    created_at: str


class AvailabilitySlot(BaseModel):
    id: int
    date: str
    start_time: str
    end_time: str
    status: str


class AvailabilityDay(BaseModel):
    date: str
    label: str
    slots: list[AvailabilitySlot]


class DoctorListItem(BaseModel):
    id: int
    name: str
    initials: str
    specialization: str
    specialization_slug: str
    qualification: str
    hospital: str
    image_url: str | None
    avatar_gradient: str
    rating: float
    review_count: int
    experience_years: int
    fee: float
    currency: str
    gender: str
    available_today: bool
    availability_label: str
    slots_today: int
    short_bio: str
    profile_url: str
    book_url: str


class DoctorProfile(DoctorListItem):
    bio: str
    education: list[str]
    working_days: list[str]
    working_hours: str
    languages: list[str]
    is_accepting_patients: bool
    is_verified: bool
    reviews: list[DoctorReviewItem]
    availability_calendar: list[AvailabilityDay]


class SpecializationOption(BaseModel):
    id: int
    name: str
    slug: str
    icon: str | None
    doctor_count: int


class DoctorDirectoryMeta(BaseModel):
    total: int
    specializations: list[SpecializationOption]
    fee_ranges: list[dict[str, str | int]] = Field(default_factory=list)
