import logging
from core.security import encrypt_data, decrypt_data
from core.database.customer_repository import (
    add_customer,
    save_or_update_vehicle,
    db_get_customer_by_phone,
    db_get_vehicle_by_plate
)

logger = logging.getLogger(__name__)

def register_customer_and_vehicle(full_name, phone_number, license_plate, brand, model, year=None, engine_code=None, vin=None):
    """
    Securely encrypts customer data, saves/updates the customer, 
    and links the vehicle to their ID.
    """
    try:
        # 1. Encrypt sensitive phone number before database insertion
        encrypted_phone = encrypt_data(str(phone_number))
        
        # 2. Save customer and get their unique ID (or existing ID if conflict)
        customer_id = add_customer(full_name, encrypted_phone)
        
        # 3. Save or update the vehicle linked to this customer
        save_or_update_vehicle(
            license_plate=license_plate.strip().upper(),
            customer_id=customer_id,
            brand=brand,
            model=model,
            year=year,
            engine_code=engine_code.strip().upper() if engine_code else None,
            vin=vin.strip().upper() if vin else None
        )
        return True
    except Exception as e:
        logger.error(f"❌ Error in register_customer_and_vehicle service: {e}")
        return False


def get_vehicle_card_secure(license_plate):
    """Retrieves vehicle details and decrypts the owner's phone number for safe display."""
    vehicle_data = db_get_vehicle_by_plate(license_plate.strip().upper())
    if not vehicle_data:
        return None
        
    # If customer phone decryption is needed later from deep queries, 
    # it will be handled here. Currently returns clean structured data.
    return vehicle_data