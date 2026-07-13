"""Landing page data provider.

Mock data for now - replace with database queries as models are built.
"""

from __future__ import annotations

from typing import Any


def get_landing_context() -> dict[str, Any]:
    """Return all data needed to render the public landing page."""
    return {
        "hero": get_hero_data(),
        "search": get_search_data(),
        "services": get_services(),
        "popular_doctors": get_popular_doctors(),
        "available_today": get_available_today(),
        "statistics": get_statistics(),
        "how_it_works": get_how_it_works(),
        "testimonials": get_testimonials(),
        "cta": get_cta_data(),
        "footer": get_footer_data(),
        "app_home": get_app_home_data(),
    }


def get_faq_page_context() -> dict[str, Any]:
    """Return data for the standalone FAQ page."""
    return {
        "faqs": get_faqs(),
        "faq_intro": get_faq_intro_data(),
        "footer": get_footer_data(),
    }


def get_app_home_data() -> dict[str, Any]:
    return {
        "greeting": "Book your doctor",
        "subtitle": "Search, compare, and book in minutes - trusted by 12,000+ patients.",
        "scroll_hint": "Scroll for more details",
        "quick_actions": [
            {
                "label": "Book Appointment",
                "url": "/register",
                "icon": "bi-calendar-plus",
                "style": "primary",
            },
            {
                "label": "Emergency",
                "url": "#available-today",
                "icon": "bi-hospital",
                "style": "emergency",
            },
        ],
    }


def get_faq_intro_data() -> dict[str, Any]:
    return {
        "title": "Got questions?",
        "subtitle": (
            "We've answered the most common questions about booking, payments, "
            "reminders, and managing your care on mediBook."
        ),
        "highlights": [
            {"icon": "bi-clock-history", "label": "Support replies within 2 hours"},
            {"icon": "bi-shield-check", "label": "Secure & encrypted health data"},
            {"icon": "bi-headset", "label": "Dedicated patient help desk"},
        ],
    }


def get_hero_data() -> dict[str, Any]:
    return {
        "badge": "Trusted by 12,000+ patients",
        "title": "Healthcare that feels",
        "title_highlight": "personal, not procedural",
        "subtitle": (
            "Book appointments with verified specialists, get timely reminders, "
            "and manage your care - all in one calm, modern platform."
        ),
        "primary_cta": {"label": "Create Free Account", "url": "/register"},
        "secondary_cta": {"label": "Find a Doctor", "url": "#search-doctors"},
        "trust_items": [
            {"icon": "bi-shield-check", "label": "Verified doctors"},
            {"icon": "bi-bell", "label": "Smart reminders"},
            {"icon": "bi-clock-history", "label": "Real-time slots"},
        ],
        "preview": {
            "patient_name": "Amina Hassan",
            "appointment": "Dr. James Mwangi",
            "specialty": "General Physician",
            "time": "Today, 2:30 PM",
            "status": "confirmed",
        },
    }


def get_search_data() -> dict[str, Any]:
    return {
        "title": "Find the right doctor",
        "subtitle": "Search by name, specialty, or hospital - see who is available today.",
        "specialties": [
            "General Physician", "Cardiologist", "Pediatrician", "Dermatologist",
            "Gynecologist", "Orthopedic", "Neurologist", "Dentist",
            "Ophthalmologist", "Psychiatrist", "Urologist", "Endocrinologist",
        ],
        "popular_searches": [
            "Cardiologist", "Pediatrician", "Dermatologist", "General Physician",
            "Gynecologist", "Dentist", "Neurologist", "Orthopedic",
            "Ophthalmologist", "Psychiatrist",
        ],
    }


def get_services() -> list[dict[str, Any]]:
    services = [
        {
            "id": "consultation",
            "icon": "bi-heart-pulse",
            "title": "Doctor Consultation",
            "short_title": "Consultation",
            "description": "In-person and follow-up visits with board-certified specialists across every major department.",
            "color": "primary",
        },
        {
            "id": "diagnostics",
            "icon": "bi-clipboard2-pulse",
            "title": "Lab & Diagnostics",
            "short_title": "Lab Tests",
            "description": "Book blood work, imaging, and screening packages with results tracked in your health timeline.",
            "color": "teal",
        },
        {
            "id": "pharmacy",
            "icon": "bi-capsule",
            "title": "Pharmacy Services",
            "short_title": "Pharmacy",
            "description": "Prescription refills and medication guidance from licensed pharmacists at partner facilities.",
            "color": "green",
        },
        {
            "id": "emergency",
            "icon": "bi-hospital",
            "title": "Emergency Care",
            "short_title": "Emergency",
            "description": "Priority routing to emergency departments with estimated wait times before you arrive.",
            "color": "amber",
        },
        {
            "id": "telehealth",
            "icon": "bi-camera-video",
            "title": "Telehealth",
            "short_title": "Telehealth",
            "description": "Secure video consultations for follow-ups, second opinions, and chronic care management.",
            "color": "primary",
        },
        {
            "id": "wellness",
            "icon": "bi-activity",
            "title": "Wellness Programs",
            "short_title": "Wellness",
            "description": "Preventive screenings, vaccination schedules, and personalized wellness plans for families.",
            "color": "teal",
        },
        {
            "id": "maternity",
            "icon": "bi-balloon-heart",
            "title": "Maternity Care",
            "description": "Prenatal check-ups, delivery planning, and postnatal support with experienced obstetricians.",
            "color": "green",
        },
        {
            "id": "mental-health",
            "icon": "bi-emoji-smile",
            "title": "Mental Health",
            "description": "Confidential counselling and psychiatric consultations with licensed mental health professionals.",
            "color": "primary",
        },
        {
            "id": "vaccination",
            "icon": "bi-shield-plus",
            "title": "Vaccination",
            "description": "Childhood immunizations, travel vaccines, and flu shots scheduled at your convenience.",
            "color": "teal",
        },
        {
            "id": "physiotherapy",
            "icon": "bi-person-arms-up",
            "title": "Physiotherapy",
            "description": "Rehabilitation sessions for injury recovery, mobility improvement, and chronic pain management.",
            "color": "amber",
        },
    ]
    for service in services:
        service.update(_SERVICE_DETAILS.get(service["id"], {}))
    return services


_SERVICE_DETAILS: dict[str, dict[str, Any]] = {
    "consultation": {
        "features": ["Board-certified specialists", "In-person & follow-up visits", "Every major department"],
        "duration": "30-45 min",
        "ideal_for": "Check-ups, referrals & chronic care",
    },
    "diagnostics": {
        "features": ["Blood work & imaging", "Results in your health timeline", "Partner lab network"],
        "duration": "15-60 min",
        "ideal_for": "Screenings, tests & monitoring",
    },
    "pharmacy": {
        "features": ["Prescription refills", "Licensed pharmacist guidance", "Partner facility pickup"],
        "duration": "10-20 min",
        "ideal_for": "Medication management & advice",
    },
    "emergency": {
        "features": ["Priority ER routing", "Estimated wait times", "24/7 partner hospitals"],
        "duration": "Immediate",
        "ideal_for": "Urgent care & emergencies",
    },
    "telehealth": {
        "features": ["Secure video calls", "Follow-ups & second opinions", "Chronic care check-ins"],
        "duration": "20-30 min",
        "ideal_for": "Remote consultations from home",
    },
    "wellness": {
        "features": ["Preventive screenings", "Vaccination schedules", "Family wellness plans"],
        "duration": "30-60 min",
        "ideal_for": "Prevention & healthy living",
    },
    "maternity": {
        "features": ["Prenatal check-ups", "Delivery planning", "Postnatal support"],
        "duration": "45-60 min",
        "ideal_for": "Pregnancy & motherhood care",
        "short_title": "Maternity",
    },
    "mental-health": {
        "features": ["Confidential sessions", "Licensed counsellors", "Psychiatric consultations"],
        "duration": "45-60 min",
        "ideal_for": "Emotional wellbeing & therapy",
        "short_title": "Mental Health",
    },
    "vaccination": {
        "features": ["Childhood immunizations", "Travel vaccines", "Flu & booster shots"],
        "duration": "15-30 min",
        "ideal_for": "Immunization & travel health",
        "short_title": "Vaccination",
    },
    "physiotherapy": {
        "features": ["Injury rehabilitation", "Mobility improvement", "Chronic pain management"],
        "duration": "45-60 min",
        "ideal_for": "Recovery & physical therapy",
        "short_title": "Physiotherapy",
    },
}


def get_available_today_page_context() -> dict[str, Any]:
    doctors = get_available_today()
    return {
        "doctors": doctors,
        "doctor_count": len(doctors),
        "total_slots": sum(d["slots_today"] for d in doctors),
        "search": get_search_data(),
        "footer": get_footer_data(),
    }


def get_popular_doctors() -> list[dict[str, Any]]:
    doctors_data = [
        (1, "Dr. Sarah Okello", "Cardiologist", "City Medical Centre", 4.9, 128, 15, 85000, True, 3),
        (2, "Dr. James Mwangi", "General Physician", "Kilimanjaro Clinic", 4.8, 96, 12, 45000, True, 5),
        (3, "Dr. Fatuma Saidi", "Pediatrician", "Hope Children's Hospital", 4.9, 214, 18, 55000, False, 0),
        (4, "Dr. Peter Kimaro", "Orthopedic Surgeon", "Orthocare Institute", 4.7, 87, 20, 95000, True, 2),
        (5, "Dr. Grace Mushi", "Dermatologist", "Skin Health Clinic", 4.8, 156, 10, 60000, True, 4),
        (6, "Dr. David Lyimo", "Neurologist", "NeuroCare Hospital", 4.9, 73, 22, 120000, True, 1),
        (7, "Dr. Neema Juma", "Gynecologist", "Women's Wellness Centre", 4.9, 189, 14, 70000, False, 0),
        (8, "Dr. Robert Msigwa", "Dentist", "Smile Dental Studio", 4.6, 112, 8, 40000, True, 6),
        (9, "Dr. Aisha Hassan", "Ophthalmologist", "Vision Plus Eye Centre", 4.8, 94, 16, 75000, True, 2),
        (10, "Dr. Emmanuel Tenga", "Psychiatrist", "MindCare Clinic", 4.9, 67, 11, 90000, True, 3),
        (11, "Dr. Christina Massawe", "Endocrinologist", "Diabetes & Hormone Centre", 4.7, 58, 13, 80000, False, 0),
        (12, "Dr. George Marwa", "Urologist", "Men's Health Institute", 4.8, 81, 17, 95000, True, 2),
    ]
    return [_doctor(*d) for d in doctors_data]


def get_available_today() -> list[dict[str, Any]]:
    return [d for d in get_popular_doctors() if d["available_today"]]


def _doctor(
    id_: int,
    name: str,
    specialization: str,
    hospital: str,
    rating: float,
    review_count: int,
    experience_years: int,
    fee: int,
    available_today: bool,
    slots_today: int,
) -> dict[str, Any]:
    initials = "".join(part[0] for part in name.replace("Dr. ", "").split()[:2])
    return {
        "id": id_,
        "name": name,
        "initials": initials,
        "specialization": specialization,
        "hospital": hospital,
        "image_url": None,
        "avatar_gradient": ["primary", "teal", "green", "amber"][id_ % 4],
        "rating": rating,
        "review_count": review_count,
        "experience_years": experience_years,
        "fee": fee,
        "currency": "TZS",
        "available_today": available_today,
        "availability_label": "Available today" if available_today else "Next: Tomorrow",
        "slots_today": slots_today,
        "profile_url": f"/doctors/{id_}",
        "book_url": f"/appointments/book?doctor={id_}",
    }


def get_statistics() -> list[dict[str, Any]]:
    return [
        {"id": "patients", "value": "12,400+", "label": "Patients served", "short_label": "Patients", "icon": "bi-people", "color": "primary"},
        {"id": "doctors", "value": "180+", "label": "Verified doctors", "short_label": "Doctors", "icon": "bi-person-badge", "color": "teal"},
        {"id": "appointments", "value": "48k", "label": "Appointments booked", "short_label": "Booked", "icon": "bi-calendar-check", "color": "green"},
        {"id": "satisfaction", "value": "98%", "label": "Patient satisfaction", "short_label": "Satisfaction", "icon": "bi-emoji-smile", "color": "amber"},
    ]


def get_how_it_works() -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "icon": "bi-search",
            "title": "Search & compare",
            "description": "Browse doctors by specialty, ratings, fees, and real-time availability at nearby hospitals.",
            "details": [
                "180+ verified specialists across partner hospitals",
                "Filter by specialty, location, fee, and rating",
                "Live slot availability updated in real time",
            ],
        },
        {
            "step": 2,
            "icon": "bi-calendar2-plus",
            "title": "Book your slot",
            "description": "Pick an open time that fits your schedule. Only available slots are selectable - no double bookings.",
            "details": [
                "Morning, afternoon, and evening slots",
                "Instant booking confirmation",
                "Automatic duplicate-booking prevention",
            ],
        },
        {
            "step": 3,
            "icon": "bi-credit-card",
            "title": "Confirm payment",
            "description": "Pay securely via M-Pesa, Mixx, Airtel Money, or other supported mobile wallets.",
            "details": [
                "M-Pesa, Mixx, Airtel Money, HaloPesa & more",
                "Secure payment with reference number",
                "Transparent fees shown before checkout",
            ],
        },
        {
            "step": 4,
            "icon": "bi-bell",
            "title": "Get reminded",
            "description": "Receive email and web notifications before your visit so you never miss an appointment.",
            "details": [
                "24-hour advance reminder",
                "2-hour follow-up alert",
                "Reschedule or cancel from your dashboard",
            ],
        },
    ]


def get_testimonials() -> list[dict[str, Any]]:
    return [
        {
            "id": 1,
            "name": "Grace Mrema",
            "role": "Patient · Dar es Salaam",
            "initials": "GM",
            "rating": 5,
            "quote": (
                "I booked a cardiologist in under two minutes. The reminder came exactly when "
                "I needed it - no more sitting in waiting rooms guessing my turn."
            ),
        },
        {
            "id": 2,
            "name": "Michael Ndege",
            "role": "Parent · Arusha",
            "initials": "MN",
            "rating": 5,
            "quote": (
                "Finding a pediatrician available the same day felt impossible before. "
                "This platform shows real slots and the doctor profiles are genuinely helpful."
            ),
        },
        {
            "id": 3,
            "name": "Halima Yusuf",
            "role": "Patient · Mwanza",
            "initials": "HY",
            "rating": 5,
            "quote": (
                "Clean interface, clear fees upfront, and payment through M-Pesa was seamless. "
                "It feels like a modern app, not a hospital bureaucracy portal."
            ),
        },
        {
            "id": 4,
            "name": "Joseph Mollel",
            "role": "Patient · Moshi",
            "initials": "JM",
            "rating": 5,
            "quote": "Rescheduling took seconds. The doctor profiles show everything I need before I book.",
        },
        {
            "id": 5,
            "name": "Elizabeth Mwakasege",
            "role": "Patient · Dodoma",
            "initials": "EM",
            "rating": 5,
            "quote": "Finally a healthcare platform that respects my time. Reminders are accurate and helpful.",
        },
        {
            "id": 6,
            "name": "Daniel Kessy",
            "role": "Parent · Tanga",
            "initials": "DK",
            "rating": 4,
            "quote": "Booked a pediatrician for my daughter on the same day. The whole family now uses mediBook.",
        },
        {
            "id": 7,
            "name": "Rehema Swai",
            "role": "Patient · Mbeya",
            "initials": "RS",
            "rating": 5,
            "quote": "Transparent pricing and verified doctors gave me confidence to switch from walk-in queues.",
        },
        {
            "id": 8,
            "name": "Patrick Shayo",
            "role": "Patient · Zanzibar",
            "initials": "PS",
            "rating": 5,
            "quote": "Telehealth follow-ups saved me a second trip to the hospital. Brilliant experience.",
        },
        {
            "id": 9,
            "name": "Christina Massawe",
            "role": "Patient · Iringa",
            "initials": "CM",
            "rating": 5,
            "quote": "The search filters make finding a specialist effortless. Registration was quick and simple.",
        },
        {
            "id": 10,
            "name": "George Marwa",
            "role": "Patient · Morogoro",
            "initials": "GM",
            "rating": 5,
            "quote": "I manage three family members' appointments from one account. Exactly what we needed.",
        },
    ]


def get_faqs() -> list[dict[str, Any]]:
    return [
        {
            "id": "booking",
            "question": "How do I book an appointment?",
            "answer": (
                "Create a free account, search for a doctor by specialty or name, "
                "select an available time slot, and confirm with payment. "
                "You'll receive instant confirmation and a reminder before your visit."
            ),
        },
        {
            "id": "cancellation",
            "question": "Can I cancel or reschedule?",
            "answer": (
                "Yes. Visit your dashboard to cancel or reschedule up to 4 hours before "
                "your appointment. Refund policies depend on the hospital's terms, "
                "which are shown before you confirm."
            ),
        },
        {
            "id": "payment",
            "question": "What payment methods are supported?",
            "answer": (
                "We support M-Pesa, Mixx by Yas, Airtel Money, HaloPesa, AzamPesa, "
                "and Selcom Pay. Payment is processed securely and you'll receive "
                "a reference number for your records."
            ),
        },
        {
            "id": "reminders",
            "question": "How do appointment reminders work?",
            "answer": (
                "You'll receive an email and web notification 24 hours before your appointment, "
                "with a follow-up reminder 2 hours prior. SMS reminders are coming soon."
            ),
        },
        {
            "id": "insurance",
            "question": "Do you accept insurance?",
            "answer": (
                "Many partner hospitals accept NHIF and private insurance. "
                "Insurance eligibility is shown on each doctor's profile. "
                "You can also pay directly via mobile money."
            ),
        },
        {
            "id": "account",
            "question": "Who can create an account?",
            "answer": (
                "Patient accounts can be created freely through our registration page. "
                "Doctor accounts are managed by hospital administrators to ensure "
                "every profile is verified before going live."
            ),
        },
        {
            "id": "data",
            "question": "Is my health data secure?",
            "answer": (
                "Yes. We use encrypted connections, secure password hashing, and "
                "session-based authentication. Your medical records are only visible "
                "to you and your treating physicians."
            ),
        },
        {
            "id": "slots",
            "question": "What if my preferred slot gets booked?",
            "answer": (
                "Only available slots are shown and selectable. If a slot is taken "
                "before you confirm, you'll see a clear message to choose another time. "
                "We prevent duplicate bookings automatically."
            ),
        },
        {
            "id": "family",
            "question": "Can I book for family members?",
            "answer": (
                "Yes. After registering, you can add family members to your patient "
                "dashboard and book appointments on their behalf."
            ),
        },
        {
            "id": "first-visit",
            "question": "What should I bring to my first visit?",
            "answer": (
                "Bring your appointment confirmation, a valid ID, any previous medical "
                "records, and your NHIF or insurance card if applicable."
            ),
        },
    ]


def get_cta_data() -> dict[str, Any]:
    return {
        "title": "Ready to take control of your health?",
        "subtitle": (
            "Join thousands of patients who book smarter, arrive on time, "
            "and never miss a follow-up."
        ),
        "primary_cta": {"label": "Get Started - It's Free", "url": "/register"},
        "secondary_cta": {"label": "Browse Doctors", "url": "#search-doctors"},
    }


def get_footer_data() -> dict[str, Any]:
    return {
        "brand": "mediBook",
        "tagline": "Modern healthcare scheduling for hospitals and patients.",
        "columns": [
            {
                "title": "Services",
                "links": [
                    {"label": "Find a Doctor", "url": "#search-doctors"},
                    {"label": "Book Appointment", "url": "/register"},
                    {"label": "Lab & Diagnostics", "url": "#services"},
                    {"label": "Telehealth", "url": "#services"},
                ],
            },
            {
                "title": "Company",
                "links": [
                    {"label": "About Us", "url": "/about"},
                    {"label": "Partner Hospitals", "url": "/partners"},
                    {"label": "Careers", "url": "/careers"},
                    {"label": "Contact", "url": "/contact"},
                ],
            },
            {
                "title": "Support",
                "links": [
                    {"label": "Help Centre", "url": "/help"},
                    {"label": "FAQs", "url": "/faq"},
                    {"label": "Privacy Policy", "url": "/privacy"},
                    {"label": "Terms of Service", "url": "/terms"},
                ],
            },
        ],
        "social": [
            {"icon": "bi-twitter-x", "url": "#", "label": "Twitter"},
            {"icon": "bi-instagram", "url": "#", "label": "Instagram"},
            {"icon": "bi-linkedin", "url": "#", "label": "LinkedIn"},
            {"icon": "bi-facebook", "url": "#", "label": "Facebook"},
        ],
        "copyright": "mediBook. All rights reserved.",
    }
