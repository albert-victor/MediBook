# Medical Appointment and Reminder System
## Project Constitution & Development Rules

Version: 1.0

---

# Project Goal

Build a modern, production-quality Medical Appointment and Reminder System for hospitals and clinics.

This project must NOT look like a university assignment.

The final product should resemble a real healthcare platform that could be deployed in production after minor improvements.

Every design and coding decision should prioritize:

- Simplicity
- Performance
- Maintainability
- User Experience
- Scalability
- Accessibility

Never prioritize complexity over usability.

---

# Core Philosophy

The system should feel

- Clean
- Professional
- Modern
- Trustworthy
- Friendly
- Fast
- Alive

The interface should never feel empty.

Instead of showing blank pages,
show meaningful content.

Every page should provide useful information immediately.

---

# UI Philosophy

Avoid dashboard templates.

Avoid AdminLTE style.

Avoid generic Bootstrap layouts.

Avoid copied SaaS templates.

Design every page uniquely.

Use proper spacing.

Use whitespace intentionally.

Prefer cards instead of tables whenever possible.

Tables should only appear where large datasets are necessary.

Every page should have visual hierarchy.

---

# Visual Style

Theme

Minimal

Healthcare

Professional

Bright

Institutional

Modern

Elegant

Light Mode only.

No Dark Mode.

---

# Color Palette

Primary

Medical Blue

Secondary

Teal

Accent

Soft Green

Background

White

Cards

Very Light Gray

Success

Green

Warning

Amber

Danger

Soft Red

Information

Blue

Never use overly saturated colors.

---

# Typography

Use modern readable fonts.

Recommended

Inter

Poppins

Nunito

Font hierarchy must be clear.

Large headings.

Comfortable paragraph spacing.

Readable line-height.

Avoid tiny fonts.

---

# Cards

Cards are the primary layout element.

Every card should have

Rounded corners

Soft shadow

Subtle hover animation

Proper padding

Good spacing

Cards should never feel crowded.

---

# Shadows

Only soft shadows.

Avoid harsh shadows.

Prefer layered elevation.

---

# Border Radius

Use consistent rounded corners.

Buttons

Cards

Inputs

Dropdowns

Modals

Everything should feel cohesive.

---

# Buttons

Primary

Secondary

Outlined

Danger

Success

Buttons should have

Hover

Focus

Pressed

Disabled states.

Use smooth transitions.

---

# Forms

Forms should feel premium.

Labels above inputs.

Proper spacing.

Helpful validation.

Clear error messages.

Good focus states.

Never overcrowd forms.

---

# Icons

Use Bootstrap Icons.

Icons should support content.

Never decorate unnecessarily.

---

# Animations

The UI should feel alive.

Use animations carefully.

Never overuse them.

Required animation principles

Scroll Reveal

Fade Up

Fade In

Slide Up

Scale In

Staggered Animation

Intersection Observer

Ease Out easing

Soft transitions

Animation duration

200ms–700ms

No flashy animations.

No bouncing effects.

No exaggerated movement.

Animations should improve experience.

---

# Scroll Reveal Rules

All major sections should animate once when entering viewport.

Use Intersection Observer.

Sections should not animate repeatedly.

Cards inside a section should reveal using staggered delays.

Example

Section

↓

Card 1

↓

Card 2

↓

Card 3

↓

Card 4

Fade Up + Stagger

---

# Hover Effects

Buttons

Cards

Doctor Cards

Service Cards

Navigation

Statistics

should respond subtly.

Use

TranslateY

Scale

Shadow

Opacity

Never overdo hover animations.

---

# Layout Rules

Use generous whitespace.

Consistent spacing.

Maximum content width.

Responsive grid.

Avoid clutter.

Avoid unnecessary borders.

Prefer cards over boxes.

---

# Navigation

Navigation should always feel simple.

Clear hierarchy.

Sticky navigation.

Active page highlighting.

Smooth scrolling.

---

# Landing Page Rules

The landing page must immediately communicate trust.

Required Sections

Hero

Search Doctor

Medical Services

Popular Doctors

Available Today

Hospital Statistics

How It Works

Testimonials

FAQ

Call To Action

Footer

Every section should reveal while scrolling.

Avoid long paragraphs.

Use illustrations and icons where appropriate.

---

# Dashboard Rules

Dashboards should never look empty.

Every dashboard should contain

Statistics

Cards

Recent Activity

Quick Actions

Useful Information

Appointments

Notifications

Calendar Summary

Upcoming Events

Avoid empty white screens.

---

# Doctor Cards

Every doctor card should include

Photo

Name

Specialization

Availability

Consultation Fee

Experience

Rating

Book Appointment Button

Cards should feel interactive.

---

# Appointment Booking

Only available slots should be selectable.

Booked slots

Disabled

Gray

Not Clickable

If another patient books the slot first

Show

"This appointment slot has already been booked.

Please choose another available slot."

Prevent duplicate bookings.

---

# Payment

Payment is simulation only.

Supported

M-Pesa

Mixx by Yas

Airtel Money

HaloPesa

AzamPesa

Selcom Pay

Show

Processing Animation

6 Seconds

Success Screen

Generate Reference Number

Save Payment.

---

# Notifications

Use toast notifications.

Success

Warning

Error

Information

Notifications should slide in smoothly.

---

# Reminder System

Automatically notify patients before appointments.

Support

Email

Web Notification

Prepare architecture for future SMS.

---

# Code Quality

Keep files small.

Single Responsibility Principle.

Reusable components.

Reusable helper functions.

No duplicated code.

Meaningful naming.

Readable code.

Comment only when necessary.

---

# HTML Rules

Semantic HTML only.

Accessible forms.

Proper heading hierarchy.

ARIA where needed.

---

# CSS Rules

Organized CSS.

Use CSS Variables.

Reusable utility classes.

No inline CSS.

Avoid !important.

Mobile-first.

---

# JavaScript Rules

Vanilla JavaScript only.

No React.

No Vue.

No Angular.

Use

Fetch API

Async Await

Modules

Reusable utilities.

No jQuery.

---

# Backend Rules

FastAPI

SQLAlchemy

SQLite

Service Layer

Repository Pattern where appropriate.

Organized routes.

Validation.

Error handling.

---

# Database Rules

SQLite

Migration-ready

Compatible with MySQL

Normalized tables.

Indexes where necessary.

No duplicated data.

---

# Responsiveness

Desktop

Laptop

Tablet

Mobile

Everything should work perfectly.

No horizontal scrolling.

---

# Accessibility

Keyboard friendly.

Visible focus.

Readable contrast.

Proper labels.

Screen reader friendly.

---

# Performance

Lazy loading where appropriate.

Optimized assets.

Minimal JavaScript.

Smooth scrolling.

Fast loading.

---

# Overall Design Goal

Every page should make users feel

"I trust this hospital."

The system should appear

Professional

Reliable

Modern

Fast

Premium

Institutional

without unnecessary complexity.

Every feature should feel intentional.

Quality is always more important than quantity.