#!/usr/bin/env python3

from sqlmodel import create_engine, Session, select
from models import ClientRegistration

# Create database connection
engine = create_engine("sqlite:///ai_call_center.db")

with Session(engine) as session:
    # Get the latest registration
    latest_registration = session.exec(
        select(ClientRegistration).order_by(ClientRegistration.created_at.desc())
    ).first()
    
    if latest_registration:
        print(f"Registration ID: {latest_registration.id}")
        print(f"Phone Number: {latest_registration.phone_number}")
        print(f"SMS Code: {latest_registration.sms_code}")
        print(f"Email: {latest_registration.email}")
        print(f"Is Completed: {latest_registration.is_completed}")
        print(f"Is Phone Verified: {latest_registration.is_phone_verified}")
    else:
        print("No registrations found")