"""Populate extended doctor profiles and patient reviews."""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Doctor, DoctorReview, User
from app.models.enums import Gender

# keyed by doctor email
PROFILE_DATA: dict[str, dict] = {
    "s.okello@medcare.com": {
        "gender": Gender.FEMALE.value,
        "qualification": "MBBS, MD (Cardiology), FACC",
        "education": ["Muhimbili University - MBBS", "University of Nairobi - MD Cardiology", "Johns Hopkins - Fellowship"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "08:00 - 16:00",
        "rating": 4.9,
        "review_count": 128,
        "short_bio": "Heart specialist focused on preventive cardiology and hypertension management for East African patients.",
        "bio": (
            "Dr. Sarah Okello is a board-certified cardiologist with over 15 years of experience treating "
            "heart conditions across Tanzania. She leads the cardiac care unit at City Medical Centre and "
            "is passionate about early detection and lifestyle-based prevention."
        ),
        "reviews": [
            ("Grace Mrema", 5, "Dr. Okello explained my ECG results clearly and adjusted my treatment plan with care."),
            ("Michael Ndege", 5, "Professional, thorough, and genuinely kind. Wait time was minimal."),
            ("Halima Yusuf", 4, "Excellent cardiologist - very knowledgeable about hypertension in our region."),
        ],
    },
    "j.mwangi@medcare.com": {
        "gender": Gender.MALE.value,
        "qualification": "MBBS, MMed (Internal Medicine)",
        "education": ["Kilimanjaro Christian Medical University - MBBS", "MUHAS - MMed Internal Medicine"],
        "languages": "English, Swahili, Kikuyu",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "working_hours": "07:30 - 15:30",
        "rating": 4.8,
        "review_count": 96,
        "short_bio": "Trusted general physician offering comprehensive primary care and chronic disease management.",
        "bio": (
            "Dr. James Mwangi provides holistic primary care at Kilimanjaro Clinic, specialising in diabetes, "
            "hypertension, and family medicine. Patients appreciate his calm manner and evidence-based approach."
        ),
        "reviews": [
            ("Joseph Mollel", 5, "My family's go-to doctor. Always listens and never rushes appointments."),
            ("Elizabeth Mwakasege", 5, "Helped me manage diabetes with a practical plan I could actually follow."),
        ],
    },
    "f.saidi@medcare.com": {
        "gender": Gender.FEMALE.value,
        "qualification": "MBBS, DCH, MRCPCH",
        "education": ["MUHAS - MBBS", "Great Ormond Street - Paediatric Fellowship"],
        "languages": "English, Swahili, Arabic",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "09:00 - 17:00",
        "rating": 4.9,
        "review_count": 214,
        "short_bio": "Compassionate pediatrician dedicated to child wellness from infancy through adolescence.",
        "bio": (
            "Dr. Fatuma Saidi has spent 18 years caring for children at Hope Children's Hospital. "
            "She specialises in growth monitoring, vaccinations, and developmental assessments."
        ),
        "reviews": [
            ("Daniel Kessy", 5, "Our daughter actually looks forward to visits. Dr. Saidi is wonderful with kids."),
            ("Rehema Swai", 5, "Explained every vaccination clearly. We trust her completely."),
        ],
    },
    "p.kimaro@medcare.com": {
        "gender": Gender.MALE.value,
        "qualification": "MBBS, MS (Orthopedics)",
        "education": ["MUHAS - MBBS", "PGIMER Chandigarh - MS Orthopedics"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "08:00 - 14:00",
        "rating": 4.7,
        "review_count": 87,
        "short_bio": "Orthopedic surgeon treating sports injuries, joint pain, and fracture recovery.",
        "bio": (
            "Dr. Peter Kimaro leads orthopaedic services at Orthocare Institute with expertise in "
            "minimally invasive joint procedures and sports medicine rehabilitation."
        ),
        "reviews": [
            ("Patrick Shayo", 5, "Fixed my knee injury and got me back to football within months."),
            ("Christina Massawe", 4, "Clear diagnosis and honest about recovery timelines."),
        ],
    },
    "g.mushi@medcare.com": {
        "gender": Gender.FEMALE.value,
        "qualification": "MBBS, MD (Dermatology)",
        "education": ["MUHAS - MBBS", "University of Cape Town - MD Dermatology"],
        "languages": "English, Swahili",
        "working_days": "Tuesday,Wednesday,Thursday,Friday,Saturday",
        "working_hours": "10:00 - 18:00",
        "rating": 4.8,
        "review_count": 156,
        "short_bio": "Dermatologist treating acne, eczema, pigmentation, and cosmetic skin concerns.",
        "bio": (
            "Dr. Grace Mushi runs Skin Health Clinic with a focus on medical and aesthetic dermatology "
            "suited to African skin types and tropical climate conditions."
        ),
        "reviews": [
            ("Amina Hassan", 5, "Finally cleared my eczema after years of failed treatments elsewhere."),
            ("Neema Juma", 5, "Professional, modern clinic, and results speak for themselves."),
        ],
    },
    "d.lyimo@medcare.com": {
        "gender": Gender.MALE.value,
        "qualification": "MBBS, DM (Neurology)",
        "education": ["MUHAS - MBBS", "AIIMS New Delhi - DM Neurology"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday",
        "working_hours": "08:30 - 15:00",
        "rating": 4.9,
        "review_count": 73,
        "short_bio": "Neurologist specialising in migraines, epilepsy, and stroke prevention.",
        "bio": (
            "Dr. David Lyimo is one of Tanzania's leading neurologists at NeuroCare Hospital, "
            "with research interests in epilepsy management and neuro-rehabilitation."
        ),
        "reviews": [
            ("George Marwa", 5, "Diagnosed my migraines accurately after years of misdiagnosis."),
        ],
    },
    "n.juma@medcare.com": {
        "gender": Gender.FEMALE.value,
        "qualification": "MBBS, MRCOG",
        "education": ["MUHAS - MBBS", "Royal College of Obstetricians - MRCOG"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "09:00 - 16:30",
        "rating": 4.9,
        "review_count": 189,
        "short_bio": "Gynecologist providing women's wellness, prenatal care, and reproductive health.",
        "bio": (
            "Dr. Neema Juma leads Women's Wellness Centre with expertise in high-risk pregnancies, "
            "fertility counselling, and minimally invasive gynaecological procedures."
        ),
        "reviews": [
            ("Halima Yusuf", 5, "Supported me through a difficult pregnancy with warmth and expertise."),
            ("Grace Mrema", 5, "The most caring gynecologist I've ever consulted."),
        ],
    },
    "r.msigwa@medcare.com": {
        "gender": Gender.MALE.value,
        "qualification": "BDS, MDS (Oral Surgery)",
        "education": ["MUHAS - BDS", "University of Pretoria - MDS"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "working_hours": "08:00 - 17:00",
        "rating": 4.6,
        "review_count": 112,
        "short_bio": "Gentle dentist offering preventive care, cosmetic dentistry, and oral surgery.",
        "bio": (
            "Dr. Robert Msigwa practices at Smile Dental Studio, known for pain-free procedures "
            "and modern cosmetic dentistry for patients of all ages."
        ),
        "reviews": [
            ("Daniel Kessy", 4, "Painless extraction and very friendly staff."),
        ],
    },
    "a.hassan@medcare.com": {
        "gender": Gender.FEMALE.value,
        "qualification": "MBBS, MS (Ophthalmology)",
        "education": ["MUHAS - MBBS", "Aravind Eye Hospital - MS Ophthalmology"],
        "languages": "English, Swahili, Arabic",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "08:00 - 16:00",
        "rating": 4.8,
        "review_count": 94,
        "short_bio": "Eye specialist for cataracts, glaucoma screening, and vision correction.",
        "bio": (
            "Dr. Aisha Hassan directs ophthalmology services at Vision Plus Eye Centre, "
            "performing cataract surgery and comprehensive eye examinations."
        ),
        "reviews": [
            ("Patrick Shayo", 5, "Cataract surgery restored my father's vision. Grateful beyond words."),
        ],
    },
    "e.tenga@medcare.com": {
        "gender": Gender.MALE.value,
        "qualification": "MBBS, MD (Psychiatry)",
        "education": ["MUHAS - MBBS", "University of Melbourne - MD Psychiatry"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "10:00 - 18:00",
        "rating": 4.9,
        "review_count": 67,
        "short_bio": "Psychiatrist providing confidential therapy for anxiety, depression, and stress.",
        "bio": (
            "Dr. Emmanuel Tenga founded MindCare Clinic to reduce mental health stigma in Tanzania. "
            "He combines medication management with cognitive behavioural therapy."
        ),
        "reviews": [
            ("Elizabeth Mwakasege", 5, "A safe space to talk. Dr. Tenga changed my life."),
            ("Rehema Swai", 5, "Compassionate and never judgmental."),
        ],
    },
    "j.bakari@medcare.com": {
        "gender": Gender.MALE.value,
        "qualification": "MBBS, MMed (Urology)",
        "education": ["MUHAS - MBBS", "University of Witwatersrand - MMed Urology"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "08:00 - 16:00",
        "rating": 4.7,
        "review_count": 58,
        "short_bio": "Urologist treating kidney stones, prostate health, and urinary conditions.",
        "bio": "Dr. John Bakari provides expert urological care at UroHealth Clinic with a patient-first approach.",
        "reviews": [("Joseph Mollel", 5, "Clear explanation and effective treatment plan.")],
    },
    "l.mwanga@medcare.com": {
        "gender": Gender.FEMALE.value,
        "qualification": "MBBS, MD (Endocrinology)",
        "education": ["MUHAS - MBBS", "University of Cape Town - MD Endocrinology"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday",
        "working_hours": "09:00 - 17:00",
        "rating": 4.8,
        "review_count": 64,
        "short_bio": "Endocrinologist specialising in diabetes, thyroid, and hormone disorders.",
        "bio": "Dr. Lucy Mwanga leads metabolic care at Metabolic Care Centre with evidence-based diabetes management.",
        "reviews": [("Amina Hassan", 5, "Helped stabilise my thyroid levels within weeks.")],
    },
    "s.rwezaula@medcare.com": {
        "gender": Gender.MALE.value,
        "qualification": "MBBS, Diploma in Family Medicine",
        "education": ["MUHAS - MBBS", "Aga Khan - Family Medicine Diploma"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "working_hours": "07:00 - 15:00",
        "rating": 4.6,
        "review_count": 42,
        "short_bio": "Community physician offering affordable primary care in Dar es Salaam.",
        "bio": "Dr. Samuel Rwezaula serves families at Muhimbili Partner Clinic with focus on preventive health.",
        "reviews": [("George Marwa", 4, "Friendly doctor, short wait times.")],
    },
    "c.mollel@medcare.com": {
        "gender": Gender.FEMALE.value,
        "qualification": "MBBS, MD (Cardiology)",
        "education": ["MUHAS - MBBS", "Groote Schuur - Cardiology Fellowship"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "08:30 - 16:30",
        "rating": 4.8,
        "review_count": 91,
        "short_bio": "Cardiologist with expertise in heart failure and preventive cardiac care.",
        "bio": "Dr. Catherine Mollel practices at HeartLink Hospital, known for thorough cardiac assessments.",
        "reviews": [("Christina Massawe", 5, "Very detailed and reassuring consultation.")],
    },
    "h.omary@medcare.com": {
        "gender": Gender.MALE.value,
        "qualification": "MBBS, DCH",
        "education": ["MUHAS - MBBS", "Red Cross War Memorial - DCH"],
        "languages": "English, Swahili, Arabic",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "09:00 - 17:00",
        "rating": 4.7,
        "review_count": 77,
        "short_bio": "Pediatrician caring for newborns, toddlers, and school-age children.",
        "bio": "Dr. Hassan Omary runs Little Stars Paediatrics with a gentle, child-friendly approach.",
        "reviews": [("Faith Mboya", 5, "My son loves visiting Dr. Omary.")],
    },
    "j.mwakyusa@medcare.com": {
        "gender": Gender.FEMALE.value,
        "qualification": "MBBS, MD (Dermatology)",
        "education": ["MUHAS - MBBS", "University of Nairobi - MD Dermatology"],
        "languages": "English, Swahili",
        "working_days": "Tuesday,Wednesday,Thursday,Friday,Saturday",
        "working_hours": "10:00 - 18:00",
        "rating": 4.7,
        "review_count": 68,
        "short_bio": "Dermatologist treating acne, hair loss, and chronic skin conditions.",
        "bio": "Dr. Judith Mwakyusa offers medical dermatology at Derma Plus Clinic.",
        "reviews": [("Lucia Tarimo", 5, "Skin cleared in under a month.")],
    },
    "f.ngowi@medcare.com": {
        "gender": Gender.MALE.value,
        "qualification": "MBBS, MRCOG",
        "education": ["MUHAS - MBBS", "Royal College of Obstetricians - MRCOG"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "08:00 - 16:00",
        "rating": 4.8,
        "review_count": 102,
        "short_bio": "Gynecologist providing prenatal, fertility, and women's health services.",
        "bio": "Dr. Frank Ngowi supports women's health at Amana Women's Hospital.",
        "reviews": [("Teresa Ngowi", 5, "Professional and respectful throughout.")],
    },
    "m.kilonzo@medcare.com": {
        "gender": Gender.FEMALE.value,
        "qualification": "MBBS, MS (Orthopedics)",
        "education": ["MUHAS - MBBS", "Christian Medical College - MS Orthopedics"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday",
        "working_hours": "08:00 - 14:00",
        "rating": 4.8,
        "review_count": 55,
        "short_bio": "Orthopedic surgeon focused on joint replacement and sports injuries.",
        "bio": "Dr. Mary Kilonzo leads orthopaedic surgery at Bone & Joint Centre.",
        "reviews": [("Patrick Shayo", 5, "Excellent surgical outcomes.")],
    },
    "p.mcharo@medcare.com": {
        "gender": Gender.MALE.value,
        "qualification": "MBBS, DM (Neurology)",
        "education": ["MUHAS - MBBS", "National Institute of Mental Health - DM Neurology"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday",
        "working_hours": "08:30 - 15:30",
        "rating": 4.9,
        "review_count": 49,
        "short_bio": "Neurologist treating epilepsy, stroke recovery, and chronic headaches.",
        "bio": "Dr. Paul Mcharo specialises in complex neurological cases at Brain & Spine Institute.",
        "reviews": [("Simon Mkumbo", 5, "Finally found relief from chronic migraines.")],
    },
    "s.rajab@medcare.com": {
        "gender": Gender.FEMALE.value,
        "qualification": "BDS, MDS",
        "education": ["MUHAS - BDS", "University of Pretoria - MDS"],
        "languages": "English, Swahili, Arabic",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "working_hours": "08:00 - 17:00",
        "rating": 4.6,
        "review_count": 88,
        "short_bio": "Dentist offering cosmetic dentistry, fillings, and family dental care.",
        "bio": "Dr. Salma Rajab practices gentle dentistry at Pearl Dental Care.",
        "reviews": [("Winnie Kavishe", 4, "Clean clinic and painless procedure.")],
    },
    "v.malima@medcare.com": {
        "gender": Gender.MALE.value,
        "qualification": "MBBS, MS (Ophthalmology)",
        "education": ["MUHAS - MBBS", "LV Prasad Eye Institute - MS Ophthalmology"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "08:00 - 16:00",
        "rating": 4.7,
        "review_count": 61,
        "short_bio": "Ophthalmologist for glaucoma, cataracts, and diabetic eye screening.",
        "bio": "Dr. Vincent Malima provides comprehensive eye care at Clear Vision Hospital.",
        "reviews": [("Victor Macha", 5, "Professional eye exam and clear advice.")],
    },
    "z.ali@medcare.com": {
        "gender": Gender.FEMALE.value,
        "qualification": "MBBS, MD (Psychiatry)",
        "education": ["MUHAS - MBBS", "University of Melbourne - MD Psychiatry"],
        "languages": "English, Swahili, Arabic",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "10:00 - 18:00",
        "rating": 4.9,
        "review_count": 54,
        "short_bio": "Psychiatrist providing therapy for anxiety, PTSD, and mood disorders.",
        "bio": "Dr. Zainab Ali leads confidential mental health care at Serenity Mental Health.",
        "reviews": [("Beatrice Shirima", 5, "Felt heard and supported from day one.")],
    },
    "t.mwambene@medcare.com": {
        "gender": Gender.MALE.value,
        "qualification": "MBBS, MMed (Internal Medicine)",
        "education": ["KCMC - MBBS", "MUHAS - MMed Internal Medicine"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "working_hours": "07:30 - 15:30",
        "rating": 4.7,
        "review_count": 83,
        "short_bio": "Experienced GP serving Arusha families with chronic disease management.",
        "bio": "Dr. Thomas Mwambene is a trusted physician at Arusha Community Clinic.",
        "reviews": [("Abel Kwayu", 5, "Knows the community and follows up diligently.")],
    },
    "r.kimathi@medcare.com": {
        "gender": Gender.FEMALE.value,
        "qualification": "MBBS, MD (Cardiology)",
        "education": ["University of Nairobi - MBBS", "MUHAS - MD Cardiology"],
        "languages": "English, Swahili, Kikuyu",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "08:00 - 16:00",
        "rating": 4.8,
        "review_count": 72,
        "short_bio": "Cardiologist specialising in hypertension and women's heart health.",
        "bio": "Dr. Rachel Kimathi practices at Coastal Cardiac Centre in Dar es Salaam.",
        "reviews": [("Zawadi Mfinanga", 5, "Thorough and caring cardiologist.")],
    },
    "i.mbena@medcare.com": {
        "gender": Gender.MALE.value,
        "qualification": "MBBS, DCH, MRCPCH",
        "education": ["CUHAS - MBBS", "MUHAS - Paediatric Residency"],
        "languages": "English, Swahili",
        "working_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "working_hours": "09:00 - 16:00",
        "rating": 4.7,
        "review_count": 66,
        "short_bio": "Pediatrician supporting child growth, immunisations, and acute illness.",
        "bio": "Dr. Issa Mbena cares for children at Mwanza Kids Care with a family-centred approach.",
        "reviews": [("Yusuf Hemed", 5, "Great with kids and very patient.")],
    },
}


def seed_doctor_profiles(db: Session) -> dict[str, int]:
    updated = 0
    reviews_added = 0

    for email, data in PROFILE_DATA.items():
        user = db.scalar(select(User).where(User.email == email))
        if not user or not user.doctor_profile:
            continue

        doctor = user.doctor_profile
        doctor.gender = data["gender"]
        doctor.qualification = data["qualification"]
        doctor.education = json.dumps(data["education"])
        doctor.languages = data["languages"]
        doctor.working_days = data["working_days"]
        doctor.working_hours = data["working_hours"]
        doctor.rating = data["rating"]
        doctor.review_count = data["review_count"]
        doctor.short_bio = data["short_bio"]
        doctor.bio = data["bio"]
        updated += 1

        existing_reviews = db.scalar(
            select(DoctorReview.id).where(DoctorReview.doctor_id == doctor.id).limit(1)
        )
        if existing_reviews:
            continue

        for patient_name, rating, comment in data["reviews"]:
            db.add(
                DoctorReview(
                    doctor_id=doctor.id,
                    patient_name=patient_name,
                    rating=rating,
                    comment=comment,
                )
            )
            reviews_added += 1

    db.commit()
    return {"profiles": updated, "reviews": reviews_added}
