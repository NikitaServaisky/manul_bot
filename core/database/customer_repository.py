import logging
from core.database import get_db

logger = logging.getLogger(__name__)

def add_customer(full_name, phone_number):
    """
    Inserts a new customer and returns their generated ID.
    If the phone number already exists, it fetches and returns the existing customer's ID.
    """
    query_insert = """
        INSERT INTO customers (full_name, phone_nubber)
        VALUES (%s, %s)
        ON CONFLICT (phone_nubber) DO NOTHING
        RETURNING id;
    """
    
    query_fetch_existing = "SELECT id FROM customers WHERE phone_nubber = %s;"
    
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Try to insert the new customer
                cursor.execute(query_insert, (full_name, phone_number))
                result = cursor.fetchone()
                
                if result:
                    conn.commit()
                    logger.info(f"✅ New customer '{full_name}' created with ID: {result[0]}")
                    return result[0]
                
                # If conflict occurred, fetch the existing customer's ID
                cursor.execute(query_fetch_existing, (phone_number,))
                existing_result = cursor.fetchone()
                if existing_result:
                    return existing_result[0]
                
    except Exception as e:
        logger.error(f"❌ Database error in add_customer: {e}")
        raise e


def save_or_update_vehicle(license_plate, customer_id, brand, model, year=None, engine_code=None, vin=None):
    """
    Inserts a new vehicle or updates its details if the license plate already exists.
    Maintains clean history and ownership changes.
    """
    query = """
        INSERT INTO vehicles (license_plate, customer_id, brand, model, year, engine_code, vin)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (license_plate) 
        DO UPDATE SET 
            brand = EXCLUDED.brand,
            model = EXCLUDED.model,
            year = EXCLUDED.year,
            engine_code = EXCLUDED.engine_code,
            vin = EXCLUDED.vin,
            customer_id = EXCLUDED.customer_id;
    """
    
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (license_plate, customer_id, brand, model, year, engine_code, vin))
                conn.commit()
                logger.info(f"✅ Vehicle {license_plate} saved/updated successfully for customer ID: {customer_id}")
                return True
    except Exception as e:
        logger.error(f"❌ Database error in save_or_update_vehicle: {e}")
        raise e


def db_get_customer_by_phone(phone_number):
    """Retrieves customer details by encrypted phone number string."""
    query = "SELECT id, full_name FROM customers WHERE phone_nubber = %s;"
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (phone_number,))
                result = cursor.fetchone()
                if result:
                    return {"id": result[0], "full_name": result[1]}
                return None
    except Exception as e:
        logger.error(f"❌ Database error in db_get_customer_by_phone: {e}")
        return None


def db_get_vehicle_by_plate(license_plate):
    """Retrieves vehicle and its owner's details using the license plate."""
    query = """
        SELECT v.license_plate, v.brand, v.model, v.year, v.engine_code, v.vin, c.full_name, c.id
        FROM vehicles v
        JOIN customers c ON v.customer_id = c.id
        WHERE v.license_plate = %s;
    """
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (license_plate,))
                result = cursor.fetchone()
                if result:
                    return {
                        "license_plate": result[0],
                        "brand": result[1],
                        "model": result[2],
                        "year": result[3],
                        "engine_code": result[4],
                        "vin": result[5],
                        "customer_name": result[6],
                        "customer_id": result[7]
                    }
                return None
    except Exception as e:
        logger.error(f"❌ Database error in db_get_vehicle_by_plate: {e}")
        return None