"""Admin dashboard - platform-wide management and analytics."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session, joinedload

from app.auth.security import hash_password
from app.config import get_settings
from app.models import (
    Admin,
    Appointment,
    Doctor,
    Notification,
    Payment,
    Specialization,
    User,
)
from app.models.enums import AppointmentStatus, PaymentStatus, UserRole
from app.schemas.admin_dashboard import (
    AdminAppointmentItem,
    AdminCharts,
    AdminDashboardOverview,
    AdminDashboardStats,
    AdminDoctorItem,
    AdminNotificationItem,
    AdminPatientItem,
    AdminPaymentItem,
    AdminReportSummary,
    AdminReportCharts,
    ChartPieItem,
    AdminSettingsView,
    ChartBarItem,
    CreateDoctorRequest,
    SpecializationOption,
    UpdateDoctorRequest,
)
from app.services.appointment_service import STATUS_LABELS
from app.services.payment_service import METHOD_LABELS, PAYMENT_STATUS_LABELS
from app.utils.exceptions import ConflictError, NotFoundError
from app.utils.helpers import ensure_utc, utcnow

settings = get_settings()


def _greeting() -> str:
    hour = utcnow().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def _month_label(year: int, month: int) -> str:
    from datetime import date
    return date(year, month, 1).strftime("%b %Y")


def _build_charts(db: Session) -> AdminCharts:
    now = utcnow()
    appt_bars: list[ChartBarItem] = []
    pay_bars: list[ChartBarItem] = []

    for i in range(5, -1, -1):
        target = now - timedelta(days=30 * i)
        year, month = target.year, target.month
        label = _month_label(year, month)

        appt_count = db.scalar(
            select(func.count(Appointment.id)).where(
                extract("year", Appointment.scheduled_start) == year,
                extract("month", Appointment.scheduled_start) == month,
            )
        ) or 0
        appt_bars.append(ChartBarItem(label=label, value=float(appt_count), display=str(appt_count)))

        revenue = db.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.COMPLETED.value,
                extract("year", Payment.paid_at) == year,
                extract("month", Payment.paid_at) == month,
            )
        ) or Decimal("0")
        rev = float(revenue)
        pay_bars.append(
            ChartBarItem(
                label=label,
                value=rev,
                display=f"TZS {rev:,.0f}",
            )
        )

    dist_rows = db.execute(
        select(Specialization.name, func.count(Doctor.id))
        .join(Doctor, Doctor.specialization_id == Specialization.id)
        .group_by(Specialization.id)
        .order_by(func.count(Doctor.id).desc())
        .limit(8)
    ).all()

    max_docs = max((row[1] for row in dist_rows), default=1) or 1
    distribution = [
        ChartBarItem(
            label=row[0],
            value=float(row[1]),
            display=str(row[1]),
        )
        for row in dist_rows
    ]

    return AdminCharts(
        appointments_per_month=appt_bars,
        payments_per_month=pay_bars,
        doctor_distribution=distribution,
    )


def _build_stats(db: Session) -> AdminDashboardStats:
    now = utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_doctors = db.scalar(select(func.count(Doctor.id))) or 0
    active_doctors = db.scalar(
        select(func.count(Doctor.id))
        .join(User, Doctor.user_id == User.id)
        .where(User.is_active.is_(True), Doctor.is_verified.is_(True))
    ) or 0

    total_patients = db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.PATIENT.value)
    ) or 0
    active_patients = db.scalar(
        select(func.count(User.id)).where(
            User.role == UserRole.PATIENT.value,
            User.is_active.is_(True),
        )
    ) or 0

    today_appts = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.scheduled_start >= today_start,
            Appointment.scheduled_start < today_end,
        )
    ) or 0

    monthly_revenue = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == PaymentStatus.COMPLETED.value,
            Payment.paid_at >= month_start,
        )
    ) or Decimal("0")

    total_appts = db.scalar(select(func.count(Appointment.id))) or 0
    pending_pay = db.scalar(
        select(func.count(Payment.id)).where(Payment.status == PaymentStatus.PENDING.value)
    ) or 0

    return AdminDashboardStats(
        total_doctors=total_doctors,
        active_doctors=active_doctors,
        total_patients=total_patients,
        active_patients=active_patients,
        today_appointments=today_appts,
        monthly_revenue=float(monthly_revenue),
        currency="TZS",
        total_appointments=total_appts,
        pending_payments=pending_pay,
    )


def get_overview(db: Session, user: User) -> AdminDashboardOverview:
    admin = db.scalar(select(Admin).where(Admin.user_id == user.id))
    return AdminDashboardOverview(
        greeting=_greeting(),
        admin_name=user.full_name,
        department=admin.department if admin else "Operations",
        job_title=admin.job_title if admin else "Administrator",
        stats=_build_stats(db),
        charts=_build_charts(db),
    )


def get_charts(db: Session) -> AdminCharts:
    return _build_charts(db)


def list_doctors(db: Session, limit: int = 50) -> list[AdminDoctorItem]:
    doctors = db.scalars(
        select(Doctor)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialization))
        .order_by(Doctor.id.desc())
        .limit(limit)
    ).unique().all()

    items = []
    for d in doctors:
        count = db.scalar(
            select(func.count(Appointment.id)).where(Appointment.doctor_id == d.id)
        ) or 0
        name = d.user.full_name if d.user else f"Doctor #{d.id}"
        if not name.startswith("Dr."):
            name = f"Dr. {name}"
        items.append(
            AdminDoctorItem(
                id=d.id,
                user_id=d.user_id,
                name=name,
                first_name=d.user.first_name if d.user else "",
                last_name=d.user.last_name if d.user else "",
                email=d.user.email if d.user else "",
                phone=d.user.phone if d.user else None,
                specialization=d.specialization.name if d.specialization else "General",
                specialization_id=d.specialization_id,
                hospital=d.hospital_name,
                license_number=d.license_number,
                consultation_fee=float(d.consultation_fee),
                currency=d.currency,
                experience_years=d.experience_years,
                is_verified=d.is_verified,
                is_accepting_patients=d.is_accepting_patients,
                is_active=d.user.is_active if d.user else False,
                appointment_count=count,
            )
        )
    return items


def create_doctor(db: Session, payload: CreateDoctorRequest) -> AdminDoctorItem:
    existing = db.scalar(select(User.id).where(User.email == payload.email.lower()))
    if existing:
        raise ConflictError("A user with this email already exists")

    license_taken = db.scalar(
        select(Doctor.id).where(Doctor.license_number == payload.license_number)
    )
    if license_taken:
        raise ConflictError("License number already registered")

    spec = db.get(Specialization, payload.specialization_id)
    if not spec:
        raise NotFoundError("Specialization not found")

    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email.lower(),
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=UserRole.DOCTOR.value,
        is_active=True,
    )
    db.add(user)
    db.flush()

    doctor = Doctor(
        user_id=user.id,
        specialization_id=payload.specialization_id,
        license_number=payload.license_number,
        hospital_name=payload.hospital_name,
        consultation_fee=Decimal(str(payload.consultation_fee)),
        experience_years=payload.experience_years,
        qualification=payload.qualification,
        is_verified=payload.is_verified,
        is_accepting_patients=payload.is_accepting_patients,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return get_doctor(db, doctor.id)


def update_doctor(db: Session, doctor_id: int, payload: UpdateDoctorRequest) -> AdminDoctorItem:
    doctor = db.scalar(
        select(Doctor)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialization))
        .where(Doctor.id == doctor_id)
    )
    if not doctor:
        raise NotFoundError("Doctor not found")

    if payload.first_name is not None:
        doctor.user.first_name = payload.first_name
    if payload.last_name is not None:
        doctor.user.last_name = payload.last_name
    if payload.phone is not None:
        doctor.user.phone = payload.phone
    if payload.specialization_id is not None:
        if not db.get(Specialization, payload.specialization_id):
            raise NotFoundError("Specialization not found")
        doctor.specialization_id = payload.specialization_id
    if payload.hospital_name is not None:
        doctor.hospital_name = payload.hospital_name
    if payload.consultation_fee is not None:
        doctor.consultation_fee = Decimal(str(payload.consultation_fee))
    if payload.experience_years is not None:
        doctor.experience_years = payload.experience_years
    if payload.qualification is not None:
        doctor.qualification = payload.qualification
    if payload.is_verified is not None:
        doctor.is_verified = payload.is_verified
    if payload.is_accepting_patients is not None:
        doctor.is_accepting_patients = payload.is_accepting_patients

    db.commit()
    return get_doctor(db, doctor_id)


def get_doctor(db: Session, doctor_id: int) -> AdminDoctorItem:
    items = [d for d in list_doctors(db, limit=200) if d.id == doctor_id]
    if not items:
        raise NotFoundError("Doctor not found")
    return items[0]


def deactivate_doctor(db: Session, doctor_id: int) -> AdminDoctorItem:
    doctor = db.scalar(
        select(Doctor).options(joinedload(Doctor.user)).where(Doctor.id == doctor_id)
    )
    if not doctor:
        raise NotFoundError("Doctor not found")
    doctor.is_accepting_patients = False
    doctor.is_verified = False
    if doctor.user:
        doctor.user.is_active = False
    db.commit()
    return get_doctor(db, doctor_id)


def delete_doctor(db: Session, doctor_id: int) -> None:
    doctor = db.scalar(
        select(Doctor).options(joinedload(Doctor.user)).where(Doctor.id == doctor_id)
    )
    if not doctor:
        raise NotFoundError("Doctor not found")

    appt_count = db.scalar(
        select(func.count(Appointment.id)).where(Appointment.doctor_id == doctor_id)
    ) or 0
    if appt_count > 0:
        raise ConflictError(
            "Cannot delete a doctor with appointment history. Deactivate instead."
        )

    user = doctor.user
    db.delete(doctor)
    if user:
        db.delete(user)
    db.commit()


def list_patients(db: Session, limit: int = 50) -> list[AdminPatientItem]:
    patients = db.scalars(
        select(User)
        .where(User.role == UserRole.PATIENT.value)
        .order_by(User.created_at.desc())
        .limit(limit)
    ).all()

    items = []
    for p in patients:
        count = db.scalar(
            select(func.count(Appointment.id)).where(Appointment.patient_id == p.id)
        ) or 0
        items.append(
            AdminPatientItem(
                id=p.id,
                name=p.full_name,
                email=p.email,
                phone=p.phone,
                is_active=p.is_active,
                appointment_count=count,
                joined_at=ensure_utc(p.created_at).isoformat(),
            )
        )
    return items


def deactivate_patient(db: Session, patient_id: int) -> AdminPatientItem:
    patient = db.get(User, patient_id)
    if not patient or patient.role != UserRole.PATIENT.value:
        raise NotFoundError("Patient not found")
    patient.is_active = False
    db.commit()
    for item in list_patients(db, limit=500):
        if item.id == patient_id:
            return item
    raise NotFoundError("Patient not found")


def list_appointments(db: Session, limit: int = 50) -> list[AdminAppointmentItem]:
    appts = db.scalars(
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.doctor).joinedload(Doctor.specialization),
            joinedload(Appointment.payment),
        )
        .order_by(Appointment.scheduled_start.desc())
        .limit(limit)
    ).unique().all()

    items = []
    for a in appts:
        patient_name = a.patient.full_name if a.patient else "Unknown"
        doc = a.doctor
        doc_name = doc.user.full_name if doc and doc.user else "Unknown"
        if doc_name and not doc_name.startswith("Dr."):
            doc_name = f"Dr. {doc_name}"
        start = ensure_utc(a.scheduled_start)
        end = ensure_utc(a.scheduled_end)
        items.append(
            AdminAppointmentItem(
                id=a.id,
                patient_name=patient_name,
                doctor_name=doc_name,
                specialization=doc.specialization.name if doc and doc.specialization else "",
                scheduled_start=start.isoformat(),
                date_label=start.strftime("%A, %d %b %Y"),
                time_range=f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}",
                status=a.status,
                status_label=STATUS_LABELS.get(a.status, a.status.title()),
                payment_status=a.payment.status if a.payment else None,
            )
        )
    return items


def list_payments(db: Session, limit: int = 50) -> list[AdminPaymentItem]:
    payments = db.scalars(
        select(Payment)
        .options(
            joinedload(Payment.appointment)
            .joinedload(Appointment.patient),
            joinedload(Payment.appointment)
            .joinedload(Appointment.doctor)
            .joinedload(Doctor.user),
        )
        .order_by(Payment.created_at.desc())
        .limit(limit)
    ).unique().all()

    items = []
    for p in payments:
        appt = p.appointment
        patient_name = appt.patient.full_name if appt and appt.patient else "-"
        doctor_name = "-"
        if appt and appt.doctor and appt.doctor.user:
            doctor_name = appt.doctor.user.full_name
            if not doctor_name.startswith("Dr."):
                doctor_name = f"Dr. {doctor_name}"
        items.append(
            AdminPaymentItem(
                id=p.id,
                appointment_id=p.appointment_id,
                patient_name=patient_name,
                doctor_name=doctor_name,
                amount=float(p.amount),
                currency=p.currency,
                method=p.payment_method,
                method_label=METHOD_LABELS.get(p.payment_method, p.payment_method),
                status=p.status,
                status_label=PAYMENT_STATUS_LABELS.get(p.status, p.status.title()),
                reference_number=p.reference_number,
                paid_at=ensure_utc(p.paid_at).isoformat() if p.paid_at else None,
            )
        )
    return items


def list_notifications(db: Session, limit: int = 30) -> list[AdminNotificationItem]:
    notes = db.scalars(
        select(Notification)
        .options(joinedload(Notification.user))
        .order_by(Notification.created_at.desc())
        .limit(limit)
    ).unique().all()

    return [
        AdminNotificationItem(
            id=n.id,
            user_name=n.user.full_name if n.user else "Unknown",
            type=n.notification_type,
            channel=n.channel,
            title=n.title,
            message=n.message[:200] + ("…" if len(n.message) > 200 else ""),
            is_read=n.is_read,
            created_at=ensure_utc(n.created_at).isoformat(),
        )
        for n in notes
    ]


def _build_report_charts(
    db: Session,
    month_start,
    new_patients: int,
    new_doctors: int,
) -> AdminReportCharts:
    status_rows = db.execute(
        select(Appointment.status, func.count(Appointment.id))
        .where(Appointment.created_at >= month_start)
        .group_by(Appointment.status)
        .order_by(func.count(Appointment.id).desc())
    ).all()
    appointment_status = [
        ChartPieItem(
            label=STATUS_LABELS.get(row[0], row[0].replace("_", " ").title()),
            value=float(row[1]),
            display=str(row[1]),
        )
        for row in status_rows
        if row[1] > 0
    ]

    method_rows = db.execute(
        select(Payment.payment_method, func.count(Payment.id))
        .where(
            Payment.status == PaymentStatus.COMPLETED.value,
            Payment.paid_at >= month_start,
        )
        .group_by(Payment.payment_method)
        .order_by(func.count(Payment.id).desc())
    ).all()
    payment_methods = [
        ChartPieItem(
            label=METHOD_LABELS.get(row[0], row[0].replace("_", " ").title()),
            value=float(row[1]),
            display=str(row[1]),
        )
        for row in method_rows
        if row[1] > 0
    ]

    platform_charts = _build_charts(db)

    return AdminReportCharts(
        appointment_status=appointment_status,
        payment_methods=payment_methods,
        appointments_trend=platform_charts.appointments_per_month,
        revenue_trend=platform_charts.payments_per_month,
        doctor_distribution=platform_charts.doctor_distribution,
        growth_comparison=[
            ChartBarItem(
                label="New Patients",
                value=float(new_patients),
                display=str(new_patients),
            ),
            ChartBarItem(
                label="New Doctors",
                value=float(new_doctors),
                display=str(new_doctors),
            ),
        ],
    )


def get_report_summary(db: Session) -> AdminReportSummary:
    now = utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_label = month_start.strftime("%B %Y")

    total = db.scalar(
        select(func.count(Appointment.id)).where(Appointment.created_at >= month_start)
    ) or 0
    completed = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.created_at >= month_start,
            Appointment.status == AppointmentStatus.COMPLETED.value,
        )
    ) or 0
    cancelled = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.created_at >= month_start,
            Appointment.status == AppointmentStatus.CANCELLED.value,
        )
    ) or 0
    revenue = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == PaymentStatus.COMPLETED.value,
            Payment.paid_at >= month_start,
        )
    ) or Decimal("0")
    new_patients = db.scalar(
        select(func.count(User.id)).where(
            User.role == UserRole.PATIENT.value,
            User.created_at >= month_start,
        )
    ) or 0
    new_doctors = db.scalar(
        select(func.count(Doctor.id)).where(Doctor.created_at >= month_start)
    ) or 0

    return AdminReportSummary(
        period_label=period_label,
        total_appointments=total,
        completed_appointments=completed,
        cancelled_appointments=cancelled,
        total_revenue=float(revenue),
        currency="TZS",
        new_patients=new_patients,
        new_doctors=new_doctors,
        charts=_build_report_charts(db, month_start, new_patients, new_doctors),
        export_ready=True,
        generated_at=now.isoformat(),
    )


def get_settings_view() -> AdminSettingsView:
    return AdminSettingsView(
        app_name=settings.app_name,
        environment=settings.app_env,
        reminder_enabled=settings.reminder_enabled,
        reminder_check_interval_minutes=settings.reminder_check_interval_minutes,
        reminder_hours_before=settings.reminder_hours_before,
        email_reminders_enabled=settings.email_reminders_enabled,
        currency="TZS",
    )


def list_specializations(db: Session) -> list[SpecializationOption]:
    specs = db.scalars(
        select(Specialization).where(Specialization.is_active.is_(True)).order_by(Specialization.name)
    ).all()
    return [SpecializationOption(id=s.id, name=s.name, slug=s.slug) for s in specs]
