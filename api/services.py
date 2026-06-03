import uuid
import random                                
from datetime import datetime, timezone     
# 💡 FIX: Added List to the typing imports so type hinting doesn't throw a NameError
from typing import Tuple, Dict, Any, List

def extract_webhook_data(payload: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    """
    Extracts the intent name, session ID, and parameters from the Dialogflow payload.
    """
    query_result = payload.get("queryResult", {})
    
    # Extract intent name
    intent_name = query_result.get("intent", {}).get("displayName", "")
    
    # Extract session ID (formats look like: "projects/.../agent/sessions/SESSION_ID")
    session_full_path = payload.get("session", "")
    session_id = session_full_path.split("/")[-1] if session_full_path else "default_session"
    
    # Extract parameters
    parameters = query_result.get("parameters", {})
    
    return intent_name, session_id, parameters

def build_fulfillment_response(text_message: str, chips: List[str] = None) -> Dict[str, Any]:
    response = {
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [text_message]
                }
            }
        ]
    }
    
    if chips and len(chips) > 0:
        response["fulfillmentMessages"].append({
            "suggestions": {
                "suggestions": [{"text": chip} for chip in chips]
            }
        })
        
    return response

def generate_order_id() -> str:
    """
    Generates an order ID based on the current timestamp.
    Example output: ORD-20260525-4821
    """
    # Modern, timezone-aware way to get UTC date string: YYYYMMDD
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    
    # Generate a random 4-digit number
    random_suffix = random.randint(1000, 9999)
    
    return f"ORD-{date_str}-{random_suffix}"

def build_product_list_response(text_message: str, prices_registry: dict) -> dict:
    options_list = []
    
    # Safeguard against missing or empty registry
    if prices_registry:
        for key, data in prices_registry.items():
            options_list.append({
                "text": data["display_name"]
            })
    
    custom_payload = {
        "richContent": [[
            {
                "type": "chips",
                "options": options_list
            }
        ]]
    }
    
    # Ensure this dictionary format matches what Dialogflow expects
    return {
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [text_message]
                }
            },
            {
                "payload": custom_payload
            }
        ]
    }
