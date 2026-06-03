from fastapi import FastAPI, Request, BackgroundTasks  
from fastapi.responses import HTMLResponse 
from fastapi.middleware.cors import CORSMiddleware
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
        # FORCE INTENT OVERRIDES BASED ON UTTERANCE CONTEXT
        # ----------------------------------------------------
        is_button_or_generic = query_text in ["find products", "find product", "products", "list products", "track orders", "track order", "checkout"]
        is_cart_action = any(word in query_text for word in ["remove", "delete", "clear", "add to cart"])

        # FIX: Force immediate mapping to order handling if it's a bare removal command 
        # This breaks Dialogflow's automatic slot-filling loop for products
        if query_text in ["remove", "delete", "remove item", "delete item"]:
            intent = "order"
            params["action"] = "remove"

        if query_text in ["clear cart", "empty cart", "clear my cart"]:
            intent = "Clear_Cart_Intent"

        # Intercept and route explicit price query tokens away from catalog matching loops
        if not is_button_or_generic and not is_cart_action and intent != "order":
            has_price_keyword = any(word in query_text for word in ["price", "cost", "how much", "rate", "value"])
            has_search_keyword = any(word in query_text for word in ["need", "want", "show me", "looking for", "find", "check", "do you have"])
            has_budget_constraint = any(word in query_text for word in ["under", "below", "less than", "budget", "around"]) or (any(char.isdigit() for char in query_text) and "k" in query_text)

            if has_price_keyword or has_budget_constraint or has_search_keyword:
                words = query_text.split()
                meaningful_words = [w for w in words if w not in ["need", "want", "find", "products", "product", "show", "me"]]
                if len(meaningful_words) > 0:
                    intent = "Check_Price_Intent"

        # ----------------------------------------------------
        # ORDER (ADD / REMOVE CART)
        # ----------------------------------------------------
        if intent == "order":
            product = params.get("products") or params.get("product")
            action = params.get("action", "add")
            raw_qty = params.get("number", 1)

            # Context Fallback: When removal action is captured
            if "remove" in query_text or "remove" in str(action).lower() or "delete" in query_text:
                if not product:
                    # Search database cart to find what they recently added
                    cart = await database.get_cart(session_id)
                    if cart and cart.get("items"):
                        # Automatically target the last added item
                        last_item = cart["items"][-1]
                        product_to_remove = last_item.get("name") or last_item.get("product_name")
                        
                        await database.remove_item_from_cart(session_id, product_to_remove)
                        return services.build_fulfillment_response(
                            f"Removed {product_to_remove} from your cart."
                        )
                    else:
                        return services.build_fulfillment_response(
                            "Your cart is currently empty! What would you like to buy?"
                        )
                
                # Explicit item extraction removal execution
                await database.remove_item_from_cart(session_id, product)
                return services.build_fulfillment_response(f"Removed {product} from your cart.")

            # Item Addition Flow
            try:
                quantity = int(raw_qty)
            except:
                quantity = 1

            if not product:
                return services.build_fulfillment_response(
                    "Which item would you like to add to your cart?"
                )

            await database.add_item_to_cart(session_id, product, quantity)
            
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
        # RECOMMEND BY BUDGET
        # ----------------------------------------------------
        elif intent == "Recommend_By_Budget_Intent":
            category = str(params.get("category", "")).lower().strip()
            budget_raw = params.get("budget")
            
            # Fallback if Dialogflow missed the exact parameters
            if not category or not budget_raw:
                return services.build_fulfillment_response(
                    "Could you specify what kind of product you are looking for and your exact budget?"
                )

            # Handle "k" formatting if passed as a string (e.g., "300k" -> 300000)
            try:
                if isinstance(budget_raw, str) and 'k' in budget_raw.lower():
                    budget_limit = int(budget_raw.lower().replace('k', '').strip()) * 1000
                else:
                    budget_limit = int(budget_raw)
            except ValueError:
                 return services.build_fulfillment_response("I couldn't quite catch that amount. What is your budget limit in numbers?")

            recommendations = []
            
            for key, data in PRICES.items():
                # Map broad categories to product keywords
                is_match = False
                if category in ["gpu", "card", "graphics card"] and any(brand in key for brand in ["nvidia", "amd", "rtx", "rx", "gtx"]):
                    is_match = True
                elif category in ["laptop", "notebook"] and any(brand in key for brand in ["asus", "lenovo", "hp", "dell"]):
                    is_match = True
                
                # Check price against budget
                if is_match:
                    try:
                        raw_price = data["price"].replace("Rs.", "").replace("(Used)", "").split("-")[0].replace(",", "").strip()
                        if int(raw_price) <= budget_limit:
                            recommendations.append(f"• {data['display_name']} ({data['price']})")
                    except:
                        continue

            # Build the response
            if recommendations:
                recs_text = "\n".join(recommendations)
                return services.build_fulfillment_response(
                    f"Here are the {category}s currently available under your budget:\n\n{recs_text}"
                )
            else:
                return services.build_fulfillment_response(
                    f"I couldn't find any {category}s strictly under Rs. {budget_limit:,}. "
                    f"Would you like to see our full list of available {category}s?"
                )
                
        # ----------------------------------------------------
        # LIST AVAILABLE PRODUCTS
        # ----------------------------------------------------
        elif intent == "List_Products_Intent" or query_text in ["find products", "products", "list products"]:
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
                cleaned = re.sub(
                    r"\b(tell me|show me|price of|what is|check|need|want|under|below|budget|looking for|find|do you have|products|product)\b",
                    "",
                    query_text
                )
                cleaned = re.sub(r"\b\d+\s*k\b", "", cleaned)
                user_input = cleaned.strip()

            clean_input = str(user_input).lower().strip()

            if not clean_input or clean_input in ["product", "products", "gpu", "card", "laptop"]:
                welcome_text = "Here are the components and laptops we currently have available:"
                return services.build_product_list_response(
                    text_message=welcome_text,
                    prices_registry=PRICES
                )

            best_match = None
            input_numbers = re.findall(r'\d+', clean_input)
            input_tokens = re.findall(r'[a-z0-9]+', clean_input)
            
            ignore_tokens = {"need", "want", "gpu", "card", "graphics", "under", "below", "k", "product", "products", "find"}
            input_tokens = [t for t in input_tokens if t not in ignore_tokens]

            for key in PRICES:
                key_tokens = re.findall(r'[a-z0-9]+', key)
                key_numbers = re.findall(r'\d+', key)
                
                if input_numbers:
                    number_match = any(num in key_numbers for num in input_numbers)
                else:
                    number_match = True

                token_match = all(token in key_tokens for token in input_tokens if not token.isdigit())

                if input_numbers and number_match and token_match:
                    best_match = key
                    break
                elif not input_numbers and token_match and len(input_tokens) > 0:
                    if any(t in key_tokens for t in input_tokens):
                        best_match = key
                        break

            if best_match:
                product = PRICES[best_match]
                budget_match = re.search(r'(\d+)\s*k', query_text)
                if budget_match:
                    user_budget = int(budget_match.group(1)) * 1000
                    try:
                        raw_market_price = product['price'].replace("Rs.", "").replace("(Used)", "").split("-")[0].replace(",", "").strip()
                        market_min_price = int(raw_market_price)
                        
                        if "under" in query_text or "below" in query_text or "budget" in query_text:
                            if user_budget < market_min_price:
                                return services.build_fulfillment_response(
                                    f"The {product['display_name']} is currently priced around {product['price']}. "
                                    f"Unfortunately, it is not available under your specified budget."
                                )
                    except:
                        pass
                
                return services.build_fulfillment_response(
                    f"The estimated price of {product['display_name']} is {product['price']}."
                )

            # Out of stock budget-handling helper routing logic
            budget_match = re.search(r'(\d+)\s*k', query_text)
            if budget_match:
                user_budget = int(budget_match.group(1)) * 1000
                alternatives = []

                for key, data in PRICES.items():
                    try:
                        raw_price = data["price"].replace("Rs.", "").replace("(Used)", "").split("-")[0].replace(",", "").strip()
                        if int(raw_price) <= user_budget + 10000:  
                            alternatives.append(data["display_name"])
                    except:
                        continue

                if alternatives:
                    alt_list = ", ".join(alternatives[:3])
                    return services.build_fulfillment_response(
                        f"I'm sorry, '{user_input.upper()}' is currently not available in our inventory.\n\n"
                        f"However, since you're shopping around that budget range, here are options we have available: {alt_list}."
                    )

            return services.build_fulfillment_response(
                f"I'm sorry, '{user_input.upper()}' is currently not available or out of stock in our inventory."
            )

        # ----------------------------------------------------
        # CLEAR CART
        # ----------------------------------------------------
        elif intent == "Clear_Cart_Intent":
            cart = await database.get_cart(session_id)
            if not cart or not cart.get("items"):
                return services.build_fulfillment_response("Your cart is already empty.")

            await database.delete_cart(session_id)
            return services.build_fulfillment_response("Your cart has been cleared successfully.")

        # ----------------------------------------------------
        # CHECKOUT
        # ----------------------------------------------------
        elif intent == "Checkout_Confirmed":
            cart = await database.get_cart(session_id)
            if not cart or not cart.get("items"):
                return services.build_fulfillment_response("Your cart is empty.")

            customer_name = None
            customer_address = None

            output_contexts = payload.get("queryResult", {}).get("outputContexts", [])
            for context in output_contexts:
                if "awaiting_checkout_confirmation" in context.get("name", "").lower():
                    context_params = context.get("parameters", {})
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

            if not customer_name or not customer_address:
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
                            raw_price = data["price"].replace("Rs.", "").replace("(Used)", "").split("-")[0].replace(",", "").strip()
                            matched_price = int(raw_price)
                        except:
                            matched_price = 0
                        break

                total_amount += matched_price * quantity

            order_id = services.generate_order_id()
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
            tracking_id = params.get("orderId") or params.get("OrderID") or params.get("order_id")

            if not tracking_id:
                return services.build_fulfillment_response("Please provide your Tracking ID.")

            tracking_id = tracking_id.strip().upper()
            order = await database.get_order(tracking_id)

            if not order:
                return services.build_fulfillment_response(f"No order found with ID {tracking_id}.")
                
            status = order.get("status", "Unknown")
            total_amount = order.get("total_amount") or order.get("totalAmount", 0) 
            created_at = order.get("created_at") or order.get("orderDate")
            customer_name = order.get("customer_name") or order.get("customerName", "N/A")
            customer_address = order.get("customer_address") or order.get("customerAddress", "N/A")

            order_date = created_at.strftime("%d %b %Y %I:%M %p") if created_at else "N/A"

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
                f"Items Ordered:\n{items_text}\n\n"
                f"💰 Total Amount: Rs. {total_amount:,}"
            )

        else:
            return services.build_fulfillment_response("I couldn't determine how to process that request.")

    except Exception as e:
        logging.error(f"Webhook Error: {str(e)}", exc_info=True)
        return services.build_fulfillment_response(f"Backend Error: {str(e)}")
