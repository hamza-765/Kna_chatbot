import uuid
import random                                      
from datetime import datetime, timezone      
from typing import Tuple, Dict, Any, List

def extract_webhook_data(payload: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    """
    Extracts the intent name, session ID, and parameters from the Dialogflow payload.
    """
    query_result = payload.get("queryResult", {})
    
    # Extract intent display name
    intent_name = query_result.get("intent", {}).get("displayName", "")
    
    # Extract session ID from the full resource path string
    session_full_path = payload.get("session", "")
    session_id = session_full_path.split("/")[-1] if session_full_path else "default_session"
    
    # Extract structural entity parameters
    parameters = query_result.get("parameters", {})
    
    return intent_name, session_id, parameters


def build_fulfillment_response(text_message: str, chips: List[str] = None) -> Dict[str, Any]:
    """
    Builds a standard text fallback block with structural suggestions.
    """
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
    Generates a unique tracking order ID string based on the current date footprint.
    Example payload structure: ORD-20260608-4821
    """
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_suffix = random.randint(1000, 9999)
    return f"ORD-{date_str}-{random_suffix}"


def build_product_list_response(text_message: str, prices_registry: dict) -> dict:
    """
    Maps your complete, uncut 21-item stock into a horizontal sliding carousel.
    Groups items 3-per-card to seamlessly pass Facebook's validation constraints.
    """
    cards = []
    all_buttons = []
    
    if prices_registry:
        for key, data in prices_registry.items():
            display_name = data["display_name"]
            
            # Clean up bloated text prefixes to target Meta's 20-character title rule
            short_title = (
                display_name.replace("Nvidia GeForce ", "")
                .replace("AMD Radeon ", "")
                .replace("Lenovo ", "")
                .replace("Super", "Sup")
            )
            short_title = short_title[:20].strip()
            
            all_buttons.append({
                "name": short_title,  # Visually safe card button label
                "action": {
                    "type": "quickReply",
                    "payload": {
                        "title": display_name,   # Trackable query parameter value
                        "message": display_name  # Text phrase fired to Dialogflow on click
                    }
                }
            })

    # Chunk the configured button arrays systematically into batches of 3 per card panel
    for i in range(0, len(all_buttons), 3):
        chunk = all_buttons[i:i+3]
        cards.append({
            "title": "Menu ",
            "subtitle": "Tap an item to view active pricing details:",
            "buttons": chunk
        })
        
    
    cards = cards[:10]

    custom_payload = {
        "platform": "kommunicate",
        "metadata": {
            "contentType": "300",
            "templateId": "10",  # Template 10 renders rich responsive carousels
            "payload": cards
        }
    }
    
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
