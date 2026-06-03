from fastapi import FastAPI, Request, BackgroundTasks  # <-- Added BackgroundTasks
from fastapi.responses import HTMLResponse, Response  
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime  
import logging
import re 
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import services
import database

app = FastAPI()

current_dir = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------
# SERVE FRONTEND HTML
# ----------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    html_path = os.path.join(current_dir, "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Frontend HTML file not found in api directory!</h1>"

# ----------------------------------------------------
# SERVE TIMER PAGE
# ----------------------------------------------------
@app.get("/timer.html", response_class=HTMLResponse)
async def serve_timer():
    timer_path = os.path.join(current_dir, "timer.html")
    if os.path.exists(timer_path):
        with open(timer_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Timer page file not found in api directory!</h1>"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# PRODUCT PRICE REGISTRY
# ----------------------------------------------------
PRICES = {
    "nvidia geforce rtx 5090": {"display_name": "Nvidia GeForce RTX 5090", "price": "Rs. 1,350,000 - 1,450,000"},
    "nvidia geforce rtx 5080": {"display_name": "Nvidia GeForce RTX 5080", "price": "Rs. 450,000 - 500,000"},
    "nvidia geforce rtx 4080 super": {"display_name": "Nvidia GeForce RTX 4080 Super", "price": "Rs. 345,000 - 365,000"},
    "amd radeon rx 7900 xtx": {"display_name": "AMD Radeon RX 7900 XTX", "price": "Rs. 310,000 - 330,000"},
    "amd radeon rx 7900 xt": {"display_name": "AMD Radeon RX 7900 XT", "price": "Rs. 260,000 - 280,000"},
    "nvidia geforce rtx 4060": {"display_name": "Nvidia GeForce RTX 4060", "price": "Rs. 95,000 - 105,000"},
    "nvidia geforce rtx 3060 ti": {"display_name": "Nvidia GeForce RTX 3060 Ti", "price": "Rs. 85,000 - 98,000 (Used)"},
    "nvidia geforce rtx 2080 ti": {"display_name": "Nvidia GeForce RTX 2080 Ti", "price": "Rs. 80,000 - 95,000 (Used)"},
    "amd radeon rx 6600 xt": {"display_name": "AMD Radeon RX 6600 XT", "price": "Rs. 65,000 - 75,000"},
    "amd radeon rx 5700 xt": {"display_name": "AMD Radeon RX 5700 XT", "price": "Rs. 48,000 - 55,000 (Used)"},
    "nvidia geforce gtx 1080 ti": {"display_name": "Nvidia GeForce GTX 1080 Ti", "price": "Rs. 50,000 - 58,000 (Used)"},
    "nvidia geforce gtx 1660 super": {"display_name": "Nvidia GeForce GTX 1660 Super", "price": "Rs. 42,000 - 48,000 (Used)"},
    "nvidia geforce gtx 1650 super": {"display_name": "Nvidia GeForce GTX 1650 Super", "price": "Rs. 30,000 - 35,000 (Used)"},
    "amd radeon rx 580": {"display_name": "AMD Radeon RX 580", "price": "Rs. 22,000 - 26,000 (Used)"},
    "asus rog zephyrus g14": {"display_name": "ASUS ROG Zephyrus G14", "price": "Rs. 475,000 - 550,000"},
    "asus rog zephyrus g14 (2022)": {"display_name": "ASUS ROG Zephyrus G14 (2022)", "price": "Rs. 240,000 - 280,000 (Used)"},
    "lenovo thinkpad x1 carbon (gen 12)": {"display_name": "Lenovo ThinkPad X1 Carbon (Gen 12)", "price": "Rs. 420,000 - 490,000"},
    "hp omnibook series": {"display_name": "HP OmniBook Series", "price": "Rs. 320,000 - 390,000"},
    "asus rog flow x13": {"display_name": "ASUS ROG Flow X13", "price": "Rs. 310,000 - 430,000"},
    "dell xps 15 (9530)": {"display_name": "Dell XPS 15 (9530)", "price": "Rs. 390,000 - 460,000"},
    "hp spectre x360 13.5": {"display_name": "HP Spectre x360 13.5", "price": "Rs. 230,000 - 290,000"}
}

# Async worker helper to prevent database engine hanging
async def save_order_async(order_id, session_id, items, total_amount, name, address):
    try:
        await database.create_order(
            order_id=order_id,
            session_id=session_id,
            items=items,
            total_amount=total_amount,
            customer_name=name,      
            customer_address=address  
        )
        await database.delete_cart(session_id)
        print(f"✅ Background Worker: Order {order_id} written successfully.")
    except Exception as db_err:
        logging.error(f"Background Database Error: {str(db_err)}")

@app.post("/webhook")
async def handle_dialogflow_webhook(request: Request, background_tasks: BackgroundTasks): 
    try:
        payload = await request.json()
        intent, session_id, params = services.extract_webhook_data(payload)

        query_text = (
            payload.get("queryResult", {})
            .get("queryText", "")
            .lower()
            .strip()
        )

        # ----------------------------------------------------
        # INTENT FIX: FORCE PRICE/BUDGET INTERCEPTION
        # ----------------------------------------------------
        # Catch words like price/cost OR patterns like "under 20k", "less than 50000"
        has_price_keyword = any(word in query_text for word in ["price", "cost", "how much"])
        has_budget_constraint = any(word in query_text for word in ["under", "below", "less than", "budget", "k"]) and any(char.isdigit() for char in query_text)

        if has_price_keyword or has_budget_constraint:
            intent = "Check_Price_Intent"

        # ----------------------------------------------------
        # ORDER (ADD / REMOVE CART)
        # ----------------------------------------------------
        if intent == "order":
            product = params.get("products") or params.get("product")
            action = params.get("action", "add")
            raw_qty = params.get("number", 1)

            try:
                quantity = int(raw_qty)
            except:
                quantity = 1

            if not product:
                return services.build_fulfillment_response(
                    "I couldn't determine the product name."
                )

            if "remove" in str(action).lower():
                await database.remove_item_from_cart(session_id, product)
                return services.build_fulfillment_response(
                    f"Removed {product} from your cart."
                )
            
            # Write to database and wait for it to finish
            await database.add_item_to_cart(session_id, product, quantity)
            
            # Construct multi-line message clearly
            bot_msg = (
                f"Added {quantity}x {product} to your cart.\n"
                f"Anything else you'd like to add or remove?\n"
                f"Perhaps you want to check the price of any product before finalizing your order?"
            )
            
            return services.build_fulfillment_response(
                text_message=bot_msg,
                chips=["Checkout", "Find Products"]
            )

        # ----------------------------------------------------
        # LIST AVAILABLE PRODUCTS
        # ----------------------------------------------------
        elif intent == "List_Products_Intent":
            welcome_text = "Here are the components and laptops we currently have available:"
            return services.build_product_list_response(
                text_message=welcome_text,
                prices_registry=PRICES
            )

        # ----------------------------------------------------
        # PRICE CHECK & BUDGET CONSTRAINTS
        # ----------------------------------------------------
        elif intent == "Check_Price_Intent":
            user_input = params.get("product") or params.get("products")

            if not user_input:
                # Clean out common question prefixes to extract the raw product name
                cleaned = re.sub(
                    r"\b(tell me|show me|price of|what is|check|need|under|below|budget|\d+k|\d+)\b",
                    "",
                    query_text
                )
                user_input = cleaned.strip()

            if not user_input:
                return services.build_fulfillment_response(
                    "Which product would you like to check out?"
                )

            clean_input = str(user_input).lower().strip()
            best_match = None

            for key in PRICES:
                if clean_input in key or key in clean_input:
                    best_match = key
                    break

            if best_match:
                product = PRICES[best_match]
                
                # Check if user mentioned an impossible budget constraint
                if "5090" in best_match and "under" in query_text:
                    return services.build_fulfillment_response(
                        f"The {product['display_name']} is currently priced around {product['price']}. "
                        f"Unfortunately, it is not available under your specified budget."
                    )
                
                return services.build_fulfillment_response(
                    f"The estimated price of {product['display_name']} is {product['price']}."
                )

            return services.build_fulfillment_response(
                f"No pricing data found for '{user_input}'."
            )

        # ----------------------------------------------------
        # CLEAR CART
        # ----------------------------------------------------
        elif intent == "Clear_Cart_Intent":
            cart = await database.get_cart(session_id)

            if not cart or not cart.get("items"):
                return services.build_fulfillment_response(
                    "Your cart is already empty."
                )

            await database.delete_cart(session_id)
            return services.build_fulfillment_response(
                "Your cart has been cleared successfully."
            )

        # ----------------------------------------------------
        # CHECKOUT
        # ----------------------------------------------------
        elif intent == "Checkout_Confirmed":
            print("\n--- CHECKOUT STARTED ---")
            cart = await database.get_cart(session_id)
            print(f"Cart retrieved for session {session_id}: {cart}")

            if not cart or not cart.get("items"):
                return services.build_fulfillment_response(
                    "Your cart is empty."
                )

            customer_name = None
            customer_address = None

            output_contexts = payload.get("queryResult", {}).get("outputContexts", [])
            for context in output_contexts:
                if "awaiting_checkout_confirmation" in context.get("name", "").lower():
                    context_params = context.get("parameters", {})
                    print(f"Found checkout context parameters: {context_params}")
                    
                    name_param = context_params.get("name")
                    customer_name = name_param.get("name") if isinstance(name_param, dict) else name_param

                    addr_param = context_params.get("address")
                    if isinstance(addr_param, dict):
                        street = addr_param.get("street-address", "").strip()
                        city = addr_param.get("city", "").strip()
                        customer_address = f"{street}, {city}" if street and city else context_params.get("address.original")
                    else:
                        customer_address = addr_param
                    break

            if not customer_name:
                top_name = params.get("name")
                customer_name = top_name.get("name") if isinstance(top_name, dict) else top_name
            
            if not customer_address:
                top_addr = params.get("address")
                customer_address = top_addr.get("street-address") if isinstance(top_addr, dict) else top_addr

            print(f"Extracted Customer: {customer_name} | Address: {customer_address}")

            if not customer_name or not customer_address:
                print("❌ Checkout failed: Missing customer name or address.")
                return services.build_fulfillment_response(
                    "I see you want to checkout, but I couldn't find your delivery details. "
                    "Could you please tell me your name and shipping address?"
                )

            total_amount = 0
            for item in cart["items"]:
                item_name = str(item.get("name") or item.get("product_name") or "").lower().strip()
                quantity = int(item.get("quantity", 1))
                matched_price = 0

                for key, data in PRICES.items():
                    if item_name in key or key in item_name:
                        try:
                            raw_price = (
                                data["price"]
                                .replace("Rs.", "")
                                .replace("(Used)", "")
                                .split("-")[0]
                                .replace(",", "")
                                .strip()
                            )
                            matched_price = int(raw_price)
                        except Exception as e:
                            print(f"Error parsing price for {key}: {e}")
                            matched_price = 0
                        break

                total_amount += matched_price * quantity

            order_id = services.generate_order_id()
            print(f"Generated Order ID: {order_id} | Total: Rs. {total_amount}")

            background_tasks.add_task(
                save_order_async,
                order_id,
                session_id,
                cart["items"],
                total_amount,
                str(customer_name).strip(),
                str(customer_address).strip()
            )

            return services.build_fulfillment_response(
                f"✅ Order placed successfully!\n\n"
                f"👤 Customer: {customer_name}\n"
                f"📍 Delivery Address: {customer_address}\n"
                f"💰 Total Amount: Rs. {total_amount:,}\n"
                f"📦 Tracking ID: {order_id}"
            )

        # ----------------------------------------------------
        # TRACK ORDER
        # ----------------------------------------------------
        elif intent == "Order_Tracking_Intent":
            tracking_id = (
                params.get("orderId")
                or params.get("OrderID")
                or params.get("order_id")
            )

            if not tracking_id:
                return services.build_fulfillment_response(
                    "Please provide your Tracking ID."
                )

            tracking_id = tracking_id.strip().upper()
            order = await database.get_order(tracking_id)

            if not order:
                return services.build_fulfillment_response(
                    f"No order found with ID {tracking_id}."
                )
            status = order.get("status", "Unknown")
            total_amount = order.get("total_amount") or order.get("totalAmount", 0) 
            created_at = order.get("created_at") or order.get("orderDate")
            customer_name = order.get("customer_name") or order.get("customerName", "N/A")
            customer_address = order.get("customer_address") or order.get("customerAddress", "N/A")

            order_date = (
                created_at.strftime("%d %b %Y %I:%M %p")
                if created_at
                else "N/A"
            )

            items = []
            for item in order.get("items", []):
                name = item.get("name") or item.get("product_name") or "Unknown Product"
                qty = item.get("quantity", 1)
                items.append(f"• {name} (Qty: {qty})")

            items_text = "\n".join(items)

            return services.build_fulfillment_response(
                f"📦 ORDER DETAILS\n\n"
                f"Tracking ID: {tracking_id}\n"
                f"Status: {status}\n"
                f"Order Date: {order_date}\n\n"
                f"👤 Customer Name: {customer_name}\n"
                f"📍 Shipping Address: {customer_address}\n\n"
                f"Items Ordered:\n"
                f"{items_text}\n\n"
                f"💰 Total Amount: Rs. {total_amount:,}"
            )

        else:
            return services.build_fulfillment_response(
                "I couldn't determine how to process that request."
            )

    except Exception as e:
        logging.error(f"Webhook Error: {str(e)}", exc_info=True)
        return services.build_fulfillment_response(f"Backend Error: {str(e)}")
