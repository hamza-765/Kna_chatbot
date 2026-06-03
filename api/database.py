import os
import datetime
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient # 🚀 Using Motor instead of standard MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise Exception("MONGO_URI environment variable is missing from the chatbot configuration!")

# Motor initializes instantly without freezing the script on cold starts
client = AsyncIOMotorClient(MONGO_URI)
db = client['knaComputers']
orders_collection = db['orders']
carts_collection = db['carts']

async def get_cart(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user's active cart from MongoDB natively using async/await."""
    cart = await carts_collection.find_one({"session_id": session_id})
    return cart if cart else {"items": []}

async def add_item_to_cart(session_id: str, product_name: str, quantity: int) -> None:
    """Adds or updates an item in the user's cart natively using async/await."""
    cart = await get_cart(session_id)
    items = cart.get("items", [])
    
    item_found = False
    for item in items:
        if item.get("name") == product_name or item.get("product_name") == product_name:
            item["quantity"] = item.get("quantity", 0) + quantity
            item_found = True
            break
            
    if not item_found:
        items.append({
            "name": product_name,
            "product_name": product_name,
            "quantity": quantity
        })
        
    await carts_collection.update_one(
        {"session_id": session_id}, 
        {"$set": {"items": items}}, 
        upsert=True
    )

async def remove_item_from_cart(session_id: str, product_name: str) -> None:
    """Removes a specific product from the cart natively using async/await."""
    cart = await get_cart(session_id)
    items = [
        item for item in cart.get("items", [])
        if item.get("name") != product_name and item.get("product_name") != product_name
    ]
    await carts_collection.update_one({"session_id": session_id}, {"$set": {"items": items}})

async def delete_cart(session_id: str) -> None:
    """Clears/Deletes a cart session natively using async/await."""
    await carts_collection.delete_one({"session_id": session_id})

async def create_order(order_id, session_id, items, total_amount, customer_name, customer_address):
    """Saves a confirmed order state natively using async/await."""
    cleaned_items = []
    for item in items:
        cleaned_items.append({
            "name": item.get("name") or item.get("product_name"),
            "quantity": int(item.get("quantity", 1)),
            "price": 0.0 
        })

    new_order = {
        "order_id": order_id,            
        "customerName": customer_name,    
        "customerAddress": customer_address,
        "session_id": session_id,
        "items": cleaned_items,
        "totalAmount": float(total_amount), 
        "status": "Processing 🚚",
        "orderDate": datetime.datetime.now(datetime.timezone.utc) # Updated modern datetime method
    }
    
    await orders_collection.insert_one(new_order)

async def get_order(order_id: str) -> Optional[Dict[str, Any]]:
    """Fetches full transaction details natively using async/await."""
    order = await orders_collection.find_one({"order_id": order_id.strip().upper()})
    return order
