import mimetypes
import logging

logger = logging.getLogger(__name__)

def process_image_for_api(image_path):
    """
    Get the path to the image and pars him to bytes, identification on bytes and returned (image_bytes, mime_type) or (none, none) on error 
    """

    try:
        # 1. Read binary
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        # 2. identificated mime type from the path
        mime_type, _ = mimetypes.guess_type(image_path)

        # if not inentificated set defult jpeg
        if not mime_type:
            mime_type= "image/jpeg"

        print(f"DEBUG: Read {len(image_bytes)} bytes, MIME: {mime_type}")
        
        return image_bytes, mime_type
    
    except FileNotFoundError:
        logger.error(f"Image not found at path: {image_path}")
        return None, None
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return None, None