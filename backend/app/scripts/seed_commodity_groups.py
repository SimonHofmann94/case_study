"""
Seed script for commodity groups.

This script populates the commodity_groups table with the standard
procurement classification categories from the Challenge specification.
"""

import uuid
from typing import List, Dict

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.commodity_group import CommodityGroup


# Commodity groups from Challenge specification (50 groups)
COMMODITY_GROUPS: List[Dict[str, str]] = [
    # General Services (001-010)
    {"category": "001", "name": "Accommodation Rentals", "description": "General Services - Accommodation and rental services"},
    {"category": "002", "name": "Membership Fees", "description": "General Services - Professional and organizational membership fees"},
    {"category": "003", "name": "Workplace Safety", "description": "General Services - Workplace safety equipment and services"},
    {"category": "004", "name": "Consulting", "description": "General Services - Business and professional consulting services"},
    {"category": "005", "name": "Financial Services", "description": "General Services - Banking, accounting, and financial services"},
    {"category": "006", "name": "Fleet Management", "description": "General Services - Vehicle fleet management and related services"},
    {"category": "007", "name": "Recruitment Services", "description": "General Services - Staffing, hiring, and recruitment services"},
    {"category": "008", "name": "Professional Development", "description": "General Services - Training, education, and professional development"},
    {"category": "009", "name": "Miscellaneous Services", "description": "General Services - Other general services not categorized elsewhere"},
    {"category": "010", "name": "Insurance", "description": "General Services - Business and liability insurance services"},

    # Facility Management (011-019)
    {"category": "011", "name": "Electrical Engineering", "description": "Facility Management - Electrical installation and maintenance"},
    {"category": "012", "name": "Facility Management Services", "description": "Facility Management - General facility management and operations"},
    {"category": "013", "name": "Security", "description": "Facility Management - Security services and systems"},
    {"category": "014", "name": "Renovations", "description": "Facility Management - Building renovations and improvements"},
    {"category": "015", "name": "Office Equipment", "description": "Facility Management - Office furniture and equipment"},
    {"category": "016", "name": "Energy Management", "description": "Facility Management - Energy efficiency and management services"},
    {"category": "017", "name": "Maintenance", "description": "Facility Management - General building maintenance services"},
    {"category": "018", "name": "Cafeteria and Kitchenettes", "description": "Facility Management - Food service areas and kitchen equipment"},
    {"category": "019", "name": "Cleaning", "description": "Facility Management - Cleaning and janitorial services"},

    # Publishing Production (020-028)
    {"category": "020", "name": "Audio and Visual Production", "description": "Publishing Production - Audio and video production services"},
    {"category": "021", "name": "Books/Videos/CDs", "description": "Publishing Production - Physical media production and publishing"},
    {"category": "022", "name": "Printing Costs", "description": "Publishing Production - Printing and reproduction services"},
    {"category": "023", "name": "Software Development for Publishing", "description": "Publishing Production - Custom software for publishing workflows"},
    {"category": "024", "name": "Material Costs", "description": "Publishing Production - Raw materials for publishing production"},
    {"category": "025", "name": "Shipping for Production", "description": "Publishing Production - Shipping and logistics for production materials"},
    {"category": "026", "name": "Digital Product Development", "description": "Publishing Production - Digital content and product development"},
    {"category": "027", "name": "Pre-production", "description": "Publishing Production - Pre-production planning and services"},
    {"category": "028", "name": "Post-production Costs", "description": "Publishing Production - Post-production editing and finishing"},

    # Information Technology (029-031)
    {"category": "029", "name": "Hardware", "description": "Information Technology - Computer hardware and equipment"},
    {"category": "030", "name": "IT Services", "description": "Information Technology - IT support and consulting services"},
    {"category": "031", "name": "Software", "description": "Information Technology - Software licenses and subscriptions"},

    # Logistics (032-035)
    {"category": "032", "name": "Courier, Express, and Postal Services", "description": "Logistics - Courier, express delivery, and postal services"},
    {"category": "033", "name": "Warehousing and Material Handling", "description": "Logistics - Warehouse storage and material handling"},
    {"category": "034", "name": "Transportation Logistics", "description": "Logistics - Transportation and freight services"},
    {"category": "035", "name": "Delivery Services", "description": "Logistics - Local and regional delivery services"},

    # Marketing & Advertising (036-043)
    {"category": "036", "name": "Advertising", "description": "Marketing & Advertising - General advertising services"},
    {"category": "037", "name": "Outdoor Advertising", "description": "Marketing & Advertising - Billboards and outdoor media"},
    {"category": "038", "name": "Marketing Agencies", "description": "Marketing & Advertising - Marketing agency services"},
    {"category": "039", "name": "Direct Mail", "description": "Marketing & Advertising - Direct mail campaigns and services"},
    {"category": "040", "name": "Customer Communication", "description": "Marketing & Advertising - Customer communication and CRM"},
    {"category": "041", "name": "Online Marketing", "description": "Marketing & Advertising - Digital and online marketing services"},
    {"category": "042", "name": "Events", "description": "Marketing & Advertising - Event planning and management"},
    {"category": "043", "name": "Promotional Materials", "description": "Marketing & Advertising - Branded merchandise and promotional items"},

    # Production (044-050)
    {"category": "044", "name": "Warehouse and Operational Equipment", "description": "Production - Equipment for warehouse and operations"},
    {"category": "045", "name": "Production Machinery", "description": "Production - Manufacturing and production machinery"},
    {"category": "046", "name": "Spare Parts", "description": "Production - Replacement parts for production equipment"},
    {"category": "047", "name": "Internal Transportation", "description": "Production - Internal logistics and material movement"},
    {"category": "048", "name": "Production Materials", "description": "Production - Raw materials for production"},
    {"category": "049", "name": "Consumables", "description": "Production - Consumable supplies for production"},
    {"category": "050", "name": "Maintenance and Repairs", "description": "Production - Equipment maintenance and repair services"},
]


def seed_commodity_groups(db: Session) -> int:
    """
    Seed commodity groups into the database.

    Args:
        db: Database session

    Returns:
        Number of commodity groups created
    """
    created_count = 0

    for group_data in COMMODITY_GROUPS:
        # Check if commodity group already exists
        existing = db.query(CommodityGroup).filter(
            CommodityGroup.category == group_data["category"]
        ).first()

        if not existing:
            commodity_group = CommodityGroup(
                id=uuid.uuid4(),
                category=group_data["category"],
                name=group_data["name"],
                description=group_data["description"],
            )
            db.add(commodity_group)
            created_count += 1

    db.commit()
    return created_count


def main():
    """Run the seed script."""
    print("Seeding commodity groups...")

    db = SessionLocal()
    try:
        count = seed_commodity_groups(db)
        print(f"Created {count} commodity groups")
        print(f"Total commodity groups in database: {db.query(CommodityGroup).count()}")
    except Exception as e:
        print(f"Error seeding commodity groups: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
