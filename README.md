Here is your updated, pro-level README.md perfectly matching your new Vercel-optimized project architecture where all application logic is housed inside the /api directory.
------------------------------
## AI Order Management Chatbot
An automated, asynchronous AI-powered conversational chatbot system that processes customer orders seamlessly through a chat interface. The system integrates Dialogflow for Natural Language Processing (NLP), Kommunicate for the frontend user interface widget, and an asynchronous FastAPI backend hosted serverless inside the /api directory on Vercel that safely streams transactions into MongoDB.
------------------------------
## 🚀 Architecture Overview

 [ User Interface ] <---> [ Kommunicate Widget ] 


                                  |
                                  v
                          [ Google Dialogflow ] (Intent Parsing)
                                  |
                                  v
                    [ Vercel Serverless Function ] (FastAPI /api/main.py)
                                  |
                                  v
                          [ MongoDB Database ] (Async Storage via Motor)


   1. Frontend (Kommunicate): Renders the user-facing chat widget on your website using a non-blocking script injection.
   2. NLU Engine (Google Dialogflow): Intercepts client-side messages, evaluates natural language user intent, and extracts structured entities (e.g., quantities, product items, and parameters).
   3. Webhook Fulfillment (FastAPI Backend): Processes high-concurrency payloads sent via Dialogflow using asynchronous routines on a serverless Vercel cloud runtime routed through the /api directory.
   4. Database Storage (MongoDB & Motor): Captures incoming transaction records asynchronously utilizing non-blocking connection pooling via the Motor driver.

------------------------------
## ✨ System Features

* Vercel Native Directory Layout: Follows Vercel's serverless standards by enclosing the application logic strictly within the /api directory for zero-config deployments.
* High-Performance Asynchronous Stack: Utilizing FastAPI and Motor prevents bottlenecking and handles concurrent chat sessions efficiently.
* Serverless Deployment Edge: Configured specifically for instant horizontal scaling and optimization on Vercel's edge architecture.
* Automated Data Validation: Integrates Pydantic for bulletproof internal request structural assertions and data integrity checking.

------------------------------
## 📁 Repository Structure

├── api/
│   ├── database.py        # Async MongoDB client setup and Motor connection pooling
│   ├── index.html         # Local HTML playground injected with the Kommunicate widget
│   ├── main.py            # FastAPI entry point, routing layer, and webhook handler
│   └── services.py        # Business workflow layer handling document formatting and DB execution
├── requirements.txt       # Production pinned Python package manifest
└── vercel.json            # Deployment configurations, serverless routes mapping, and Python runtime

------------------------------
## 🛠️ Prerequisites
Ensure your environment satisfies the following workspace targets:

* Python 3.10+ local execution runtime
* A live MongoDB Atlas cloud deployment cluster URI
* A configured Google Dialogflow ES/CX conversation agent console profile
* A verified Kommunicate Dashboard active software token

------------------------------
## 🔧 Installation & Local Environment Setup## 1. Clone the Repository

git clone [https://github.com](https://github.com/hamza-765/Kna_chatbot)
cd your-repo-name

## 2. Prepare Dependencies and Virtual Environment

# Create environment
python -m venv venv
# Activate shell environment (Linux/macOS)
source venv/bin/activate
# Activate shell environment (Windows CMD)
venv\Scripts\activate
# Apply explicit project dependencies from the root directory
pip install -r requirements.txt

## 3. Establish Local Environment Context
Create a .env deployment file inside the repository root directory:

MONGO_URI=mongodb+srv://<db_user>:<db_password>@cluster.mongodb.net/
DB_NAME=orders_db

## 4. Boot Up the Local Uvicorn Development Web Server

uvicorn api.main:app --reload --port 8000

Your local server health endpoint will actively listen at http://localhost:8000/.
------------------------------
## 🌐 Webhook Integration & Cloud Deployment Steps## Step 1: Connect Dialogflow to the FastAPI Engine

   1. Deploy the app infrastructure using the Vercel cloud pipeline (vercel command) to obtain your secure live canonical URL.
   2. Enter the Dialogflow Console interface and select your operational Agent.
   3. Access the Fulfillment configuration parameters using the primary left-hand dashboard column.
   4. Enable the native Webhook service component toggle switch.
   5. Inject your live Vercel route target path into the designated input text block (e.g., https://vercel.app or https://vercel.app depending on your vercel.json routing configuration).
   6. Navigate to your target custom order placement intents and enable the checkbox labeled "Enable webhook call for this intent".

## Step 2: Inject the Frontend Customer Widget

   1. Access the Kommunicate Dashboard, move into the Bot Integrations pane, and sync your designated Dialogflow instance.
   2. Download your production unique JavaScript token embed script code block from the setup interface.
   3. Replace the placeholder token inside your api/index.html file layout component before your primary closing body tag context.

------------------------------
## 📊 Database Document Schema Blueprint
When an order intent handles successful processing, documents append cleanly to your MongoDB collection following this schema layout:

{
  "_id": { "$oid": "6664ab620a2e724bc24bf81c" },
  "customer_name": "Jane Doe",
  "items": [
    {
      "product_name": "Espresso",
      "quantity": 3,
      "size": "Regular"
    }
  ],
  "order_status": "Pending",
  "timestamp": "2026-06-08T19:09:00Z"
}

------------------------------
## 🤝 Contribution Strategy

   1. Fork the upstream repository asset directory.
   2. Create an isolated descriptive execution feature path branch (git checkout -b feature/AmazingNewFeature).
   3. Commit localized functional updates cleanly (git commit -m 'Implement an AmazingNewFeature addition').
   4. Push programmatic context changes cleanly to origin track (git push origin feature/AmazingNewFeature).
   5. Open an official upstream evaluation Pull Request for comprehensive reviewer feedback.

------------------------------
## 📄 License
Distributed under the terms of the MIT License. See individual repository metadata files for additional terms.
------------------------------
Now that your repository layout is clean, do you need help building out the exact JSON contents for your simplified vercel.json file to handle your new /api routes correctly, or do you want to implement CORS middleware inside main.py to let your local index.html contact your backend safely?

