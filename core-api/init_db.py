#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the database with sample data for testing
the AI Call Center system functionality.
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from sqlmodel import SQLModel, create_engine, Session, select
from passlib.context import CryptContext

from models import (
    Tenant, User, Modem, AdminSettings, AIToolConfig,
    UserRole, ModemStatus, PhoneNumberType
)
from config import CoreAPIConfig


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def init_database():
    """Initialize database with sample data."""
    print("🚀 Initializing AI Call Center database...")
    
    # Create database engine
    config = CoreAPIConfig()
    engine = create_engine("sqlite:///./ai_call_center.db", echo=True)
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables created")
    
    with Session(engine) as session:
        # Check if default tenant already exists
        existing_tenant = session.exec(select(Tenant).where(Tenant.slug == "demo")).first()
        if not existing_tenant:
            # Create default tenant
            default_tenant = Tenant(
                name="AI Call Center Demo",
                slug="demo",
                email="admin@demo.com",
                status="active",
                subscription_plan="enterprise",
                max_concurrent_calls=80,
                max_daily_calls=10000,
                max_sms_per_day=5000,
                max_users=50,
                max_modems=80,
                industry="Technology",
                company_size="Medium",
                timezone="UTC",
                currency="USD",
                gemini_api_key="demo-api-key",
                features_enabled={
                    "ai_assistant": True,
                    "sms_verification": True,
                    "temporary_numbers": True,
                    "subscription_management": True,
                    "admin_panel": True
                }
            )
            session.add(default_tenant)
            session.commit()
            session.refresh(default_tenant)
            print(f"✅ Created default tenant: {default_tenant.name}")
        else:
            default_tenant = existing_tenant
            print(f"✅ Default tenant already exists: {default_tenant.name}")
        
        # Check if admin user already exists
        existing_admin = session.exec(select(User).where(User.email == "admin@demo.com")).first()
        if not existing_admin:
            # Create admin user
            admin_user = User(
                email="admin@demo.com",
                username="admin",
                first_name="Admin",
                last_name="User",
                password_hash=hash_password("admin123"),
                phone="+1234567890",
                role=UserRole.SUPER_ADMIN,
                is_active=True,
                is_verified=True,
                tenant_id=default_tenant.id
            )
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            print(f"✅ Created admin user: {admin_user.email} (password: admin123)")
        else:
            print(f"✅ Admin user already exists: {existing_admin.email}")
        
        # Create sample modems
        sample_modems = [
            # Company numbers (for temporary assignments)
            {
                "modem_id": "COMP_001",
                "phone_number": "+1555-COMPANY-1",
                "phone_number_type": PhoneNumberType.COMPANY,
                "status": ModemStatus.AVAILABLE,
                "gemini_api_key": "demo-gemini-key-1"
            },
            {
                "modem_id": "COMP_002", 
                "phone_number": "+1555-COMPANY-2",
                "phone_number_type": PhoneNumberType.COMPANY,
                "status": ModemStatus.AVAILABLE,
                "gemini_api_key": "demo-gemini-key-2"
            },
            {
                "modem_id": "COMP_003",
                "phone_number": "+1555-COMPANY-3", 
                "phone_number_type": PhoneNumberType.COMPANY,
                "status": ModemStatus.AVAILABLE,
                "gemini_api_key": "demo-gemini-key-3"
            },
            # Client numbers (for permanent assignments)
            {
                "modem_id": "CLIENT_001",
                "phone_number": "+1555-CLIENT-01",
                "phone_number_type": PhoneNumberType.CLIENT,
                "status": ModemStatus.AVAILABLE,
                "gemini_api_key": "demo-gemini-key-4"
            },
            {
                "modem_id": "CLIENT_002",
                "phone_number": "+1555-CLIENT-02", 
                "phone_number_type": PhoneNumberType.CLIENT,
                "status": ModemStatus.AVAILABLE,
                "gemini_api_key": "demo-gemini-key-5"
            },
            {
                "modem_id": "CLIENT_003",
                "phone_number": "+1555-CLIENT-03",
                "phone_number_type": PhoneNumberType.CLIENT,
                "status": ModemStatus.AVAILABLE,
                "gemini_api_key": "demo-gemini-key-6"
            },
            {
                "modem_id": "CLIENT_004",
                "phone_number": "+1555-CLIENT-04",
                "phone_number_type": PhoneNumberType.CLIENT,
                "status": ModemStatus.AVAILABLE,
                "gemini_api_key": "demo-gemini-key-7"
            },
            {
                "modem_id": "CLIENT_005",
                "phone_number": "+1555-CLIENT-05",
                "phone_number_type": PhoneNumberType.CLIENT,
                "status": ModemStatus.AVAILABLE,
                "gemini_api_key": "demo-gemini-key-8"
            }
        ]
        
        # Check if modems already exist
        existing_modems = session.exec(select(Modem)).all()
        if not existing_modems:
            for modem_data in sample_modems:
                modem = Modem(
                    modem_id=modem_data["modem_id"],
                    phone_number=modem_data["phone_number"],
                    phone_number_type=modem_data["phone_number_type"],
                    status=modem_data["status"],
                    is_active=True,
                    gemini_api_key=modem_data["gemini_api_key"],
                    ai_prompt="You are a helpful AI assistant for business automation.",
                    device_info={
                        "model": "SIM900",
                        "firmware": "1.0.0",
                        "location": "Server Room"
                    },
                    signal_strength=85,
                    uptime_percentage=99.5
                )
                session.add(modem)
            
            session.commit()
            print(f"✅ Created {len(sample_modems)} sample modems")
        else:
            print(f"✅ Modems already exist: {len(existing_modems)} modems found")
        
        # Create admin settings
        admin_settings = [
            {
                "setting_key": "default_gemini_api_key",
                "setting_value": "demo-default-gemini-key",
                "setting_type": "string",
                "description": "Default Gemini API key for new modems",
                "category": "ai_configuration",
                "is_sensitive": True
            },
            {
                "setting_key": "max_concurrent_calls",
                "setting_value": "80",
                "setting_type": "integer", 
                "description": "Maximum concurrent calls across all modems",
                "category": "system_limits",
                "is_sensitive": False
            },
            {
                "setting_key": "temporary_assignment_duration",
                "setting_value": "30",
                "setting_type": "integer",
                "description": "Duration in minutes for temporary phone assignments",
                "category": "system_configuration",
                "is_sensitive": False
            },
            {
                "setting_key": "sms_verification_timeout",
                "setting_value": "10",
                "setting_type": "integer",
                "description": "SMS verification timeout in minutes",
                "category": "authentication",
                "is_sensitive": False
            },
            {
                "setting_key": "subscription_monthly_price",
                "setting_value": "99.99",
                "setting_type": "float",
                "description": "Monthly subscription price in USD",
                "category": "billing",
                "is_sensitive": False
            }
        ]
        
        # Check if admin settings already exist
        existing_settings = session.exec(select(AdminSettings)).all()
        if not existing_settings:
            for setting_data in admin_settings:
                setting = AdminSettings(
                    setting_key=setting_data["setting_key"],
                    setting_value=setting_data["setting_value"],
                    setting_type=setting_data["setting_type"],
                    description=setting_data["description"],
                    category=setting_data["category"],
                    is_sensitive=setting_data["is_sensitive"]
                )
                session.add(setting)
            
            session.commit()
            print(f"✅ Created {len(admin_settings)} admin settings")
        else:
            print(f"✅ Admin settings already exist: {len(existing_settings)} settings found")
        
    print("\n🎉 Database initialization completed successfully!")
    print("\n📋 Demo Credentials:")
    print("   Admin Email: admin@demo.com")
    print("   Admin Password: admin123")
    print("\n🌐 Access URLs:")
    print("   Client Registration: http://localhost:8000/")
    print("   Admin Panel: http://localhost:8000/static/admin.html")
    print("   API Documentation: http://localhost:8000/docs")
    print("\n🚀 Start the server with: uvicorn main:app --host 0.0.0.0 --port 8000 --reload")


if __name__ == "__main__":
    init_database()