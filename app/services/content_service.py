"""Static content for legal, partners, and informational pages."""

from typing import Any

PRIVACY_SECTIONS: list[dict[str, Any]] = [
    {
        "id": "overview",
        "title": "Overview",
        "paragraphs": [
            "mediBook helps patients discover verified doctors, book appointments, and manage care online. "
            "This Privacy Policy explains what personal data we collect, how we use it, and the choices you have.",
            "By using mediBook you agree to the practices described here. If you do not agree, please do not use the platform.",
        ],
    },
    {
        "id": "data-we-collect",
        "title": "Information we collect",
        "paragraphs": [
            "Account details such as your name, email address, phone number, and password (stored securely as a hash).",
            "Appointment information including doctor selected, date and time, visit reason, and payment references.",
            "Doctor profile data submitted during registration or application, including medical licence numbers and hospital affiliation.",
            "Technical data such as browser type, device information, and usage logs used to keep the service secure and reliable.",
        ],
    },
    {
        "id": "how-we-use",
        "title": "How we use your information",
        "paragraphs": [
            "To create and manage your account, process bookings, send appointment reminders, and display your dashboard.",
            "To verify doctor credentials before profiles are published to patients.",
            "To process simulated or live payments and provide receipts and transaction references.",
            "To improve platform performance, prevent fraud, and comply with applicable healthcare and data-protection laws.",
        ],
    },
    {
        "id": "sharing",
        "title": "When we share information",
        "paragraphs": [
            "We share booking details with the doctor and hospital involved in your appointment so they can provide care.",
            "We may share data with payment processors when you complete a transaction.",
            "We do not sell your personal information. We may disclose data when required by law or to protect the safety of users.",
        ],
    },
    {
        "id": "retention",
        "title": "Data retention and security",
        "paragraphs": [
            "We retain account and appointment records for as long as your account is active and as needed for legal, billing, and care-coordination purposes.",
            "We apply industry-standard safeguards including encrypted passwords, access controls, and secure hosting practices.",
            "No online system is completely secure. Please use a strong password and keep your login details confidential.",
        ],
    },
    {
        "id": "your-rights",
        "title": "Your choices and rights",
        "paragraphs": [
            "You may update profile information from your dashboard or contact support to request corrections.",
            "You may request account deletion subject to records we must keep for legal or medical purposes.",
            "You can manage notification preferences where available in your account settings.",
        ],
    },
    {
        "id": "contact",
        "title": "Contact us",
        "paragraphs": [
            "Questions about this policy can be sent to privacy@medibook.co.tz or through the Contact page on this website.",
            "We may update this policy from time to time. Material changes will be posted on this page with an updated effective date.",
        ],
    },
]

TERMS_SECTIONS: list[dict[str, Any]] = [
    {
        "id": "acceptance",
        "title": "Acceptance of terms",
        "paragraphs": [
            "These Terms of Service govern your use of mediBook. By creating an account or booking an appointment you agree to these terms.",
            "If you are using mediBook on behalf of a hospital or clinic, you confirm that you have authority to bind that organisation.",
        ],
    },
    {
        "id": "services",
        "title": "Our services",
        "paragraphs": [
            "mediBook provides an online scheduling platform connecting patients with verified healthcare providers at partner hospitals.",
            "We facilitate discovery, booking, reminders, and payment references. mediBook does not provide medical advice or emergency care.",
            "For medical emergencies, contact local emergency services immediately.",
        ],
    },
    {
        "id": "accounts",
        "title": "Accounts and eligibility",
        "paragraphs": [
            "Patients may register directly. Doctor accounts are created through application and must be verified by mediBook administrators before appearing publicly.",
            "You are responsible for keeping your login credentials secure and for all activity under your account.",
            "You agree to provide accurate information and to update it when it changes.",
        ],
    },
    {
        "id": "appointments",
        "title": "Appointments and cancellations",
        "paragraphs": [
            "Confirmed appointments are subject to the doctor's availability and hospital policies shown at booking time.",
            "Patients may cancel or reschedule from their dashboard according to the cancellation window displayed during booking.",
            "Refunds, where applicable, follow the partner hospital's policy disclosed before payment.",
        ],
    },
    {
        "id": "payments",
        "title": "Payments",
        "paragraphs": [
            "Fees displayed on doctor profiles are set by providers and may change. The amount due is shown before you confirm payment.",
            "Payment references generated through the platform must be kept for your records.",
            "mediBook is not responsible for mobile-money network outages beyond our reasonable control.",
        ],
    },
    {
        "id": "conduct",
        "title": "Acceptable use",
        "paragraphs": [
            "You may not misuse the platform, attempt unauthorised access, submit false medical credentials, or harass other users.",
            "We may suspend or terminate accounts that violate these terms or pose a risk to patients or providers.",
        ],
    },
    {
        "id": "liability",
        "title": "Disclaimer and limitation of liability",
        "paragraphs": [
            "Healthcare services are delivered by licensed professionals and partner hospitals, not by mediBook itself.",
            "The platform is provided as is to the extent permitted by law. We do not guarantee uninterrupted availability.",
            "To the maximum extent allowed by applicable law, mediBook is not liable for indirect or consequential damages arising from use of the service.",
        ],
    },
    {
        "id": "changes",
        "title": "Changes to these terms",
        "paragraphs": [
            "We may revise these terms periodically. Continued use after changes are posted constitutes acceptance of the updated terms.",
            "For questions, contact legal@medibook.co.tz.",
        ],
    },
]

PARTNER_HOSPITALS: list[dict[str, Any]] = [
    {"name": "City Medical Centre", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Cardiology", "General medicine", "Diagnostics"]},
    {"name": "Muhimbili Partner Clinic", "city": "Dar es Salaam", "region": "Coast", "specialties": ["General medicine", "Paediatrics"]},
    {"name": "Hope Children's Hospital", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Paediatrics", "Vaccination"]},
    {"name": "HeartLink Hospital", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Cardiology", "Emergency"]},
    {"name": "NeuroCare Hospital", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Neurology", "Rehabilitation"]},
    {"name": "Women's Wellness Centre", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Gynaecology", "Maternity"]},
    {"name": "Amana Women's Hospital", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Gynaecology", "Obstetrics"]},
    {"name": "Orthocare Institute", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Orthopaedics", "Physiotherapy"]},
    {"name": "Bone & Joint Centre", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Orthopaedics", "Sports medicine"]},
    {"name": "Vision Plus Eye Centre", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Ophthalmology", "Optometry"]},
    {"name": "Clear Vision Hospital", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Ophthalmology"]},
    {"name": "MindCare Clinic", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Psychiatry", "Counselling"]},
    {"name": "Serenity Mental Health", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Psychiatry", "Telehealth"]},
    {"name": "Kilimanjaro Clinic", "city": "Moshi", "region": "Kilimanjaro", "specialties": ["General medicine", "Travel health"]},
    {"name": "Arusha Community Clinic", "city": "Arusha", "region": "Arusha", "specialties": ["General medicine", "Family care"]},
    {"name": "Coastal Cardiac Centre", "city": "Tanga", "region": "Tanga", "specialties": ["Cardiology", "Diagnostics"]},
    {"name": "Mwanza Kids Care", "city": "Mwanza", "region": "Mwanza", "specialties": ["Paediatrics", "Immunisation"]},
    {"name": "Skin Health Clinic", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Dermatology", "Cosmetic care"]},
    {"name": "Smile Dental Studio", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Dentistry", "Oral surgery"]},
    {"name": "Pearl Dental Care", "city": "Dar es Salaam", "region": "Coast", "specialties": ["Dentistry"]},
]

CAREERS_STEPS: list[dict[str, str]] = [
    {
        "icon": "bi-file-earmark-person",
        "title": "Submit your application",
        "description": "Complete the form with your credentials, licence number, and hospital affiliation.",
    },
    {
        "icon": "bi-shield-check",
        "title": "Admin verification",
        "description": "Our team reviews your medical licence and profile details before approval.",
    },
    {
        "icon": "bi-person-check",
        "title": "Go live for patients",
        "description": "Once verified, your profile appears in the directory and you can accept appointments.",
    },
]


def get_privacy_content() -> dict[str, Any]:
    return {"sections": PRIVACY_SECTIONS, "updated": "July 2026"}


def get_terms_content() -> dict[str, Any]:
    return {"sections": TERMS_SECTIONS, "updated": "July 2026"}


def get_partners_content() -> dict[str, Any]:
    return {"hospitals": PARTNER_HOSPITALS, "count": len(PARTNER_HOSPITALS)}


def get_careers_content() -> dict[str, Any]:
    return {"steps": CAREERS_STEPS}
