import uuid
import random                                
from datetime import datetime, timezone     
from typing import Tuple, Dict, Any, List

def extract_webhook_data(payload: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    """
    Extracts the intent name, session ID, and parameters from the Dialogflow payload.
    """
    query_result = payload.get("queryResult", {})
    
    
    intent_name = query_result.get("intent", {}).get("displayName", "")
    
    
    session_full_path = payload.get("session", "")
    session_id = session_full_path.split("/")[-1] if session_full_path else "default_session"
    
    
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
    
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    
    
    random_suffix = random.randint(1000, 9999)
    
    return f"ORD-{date_str}-{random_suffix}"

def build_product_list_response(text_message: str, prices_registry: dict) -> dict:
    options_list = []
    
    if prices_registry:
        for key, data in prices_registry.items():
            display_name = data["display_name"]
            
            
            short_title = (
                display_name.replace("Nvidia GeForce ", "")
                .replace("AMD Radeon ", "")
                .replace("Lenovo ", "")
                .replace("Super", "Sup")
            )
            
            
            short_title = short_title[:20].strip()
            
            options_list.append({
                "title": short_title,     
                "message": display_name   
            })
            
    
    options_list = options_list[:11]
    
    custom_payload = {
        "message": text_message,
        "platform": "kommunicate",
        "metadata": {
            "contentType": "300",
            "templateId": "6",
            "payload": options_list
        }
    }
    
    return {
        "fulfillmentMessages": [
            {
                "payload": custom_payload
            }
        ]
    }
