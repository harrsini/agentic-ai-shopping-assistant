#🤖 Agentic AI Shopping Assistant

An AI-powered conversational shopping assistant that combines LargeLanguage Models, traditional Machine Learning, historicalcustomer/product data, and product retrieval to help users makepersonalized beauty-product purchasing decisions.

Instead of relying on traditional keyword-based product search, userscan describe their needs naturally --- such as their skin type,preferences, concerns, or budget --- and the assistant interprets therequest, evaluates relevant products, ranks them using an XGBoost model,and uses LLM reasoning to provide recommendations and explanations.

✨ Overview

The Agentic AI Shopping Assistant uses a hybrid AI architecture wheredifferent technologies perform different responsibilities:

Groq Llama 3.3 70B --- natural-language understanding, intentextraction, routing, reasoning, comparison, and response generation

MongoDB Atlas --- product and historical customer-review datastorage

XGBoost --- data-driven product scoring and ranking

FastAPI --- backend API and workflow orchestration

React --- conversational user interface and productvisualization

The system supports three major workflows:

🛍️ Personalized Product Recommendations

⚖️ Product Comparisons

💡 Product Information & Q&A

🧠 Why Agentic AI?

A traditional shopping application might follow:

User Query
    ↓
Keyword Search
    ↓
Database
    ↓
Products

This project follows a more intelligent workflow:

User Query
    ↓
LLM Intent Understanding
    ↓
Intent Routing
    ├── Recommendation
    │      ↓
    │  Candidate Retrieval
    │      ↓
    │  XGBoost Ranking
    │      ↓
    │  LLM Reasoning
    │      ↓
    │  Personalized Recommendations
    │
    ├── Comparison
    │      ↓
    │  LLM Comparison
    │
    └── Information
           ↓
       LLM Response

The key idea is to give each component a specific responsibility ratherthan treating the LLM, database, or ML model as the entirerecommendation system.

🛍️ What Can It Do?

Personalized Recommendations

Users can ask natural-language questions such as:

I have dry skin. Which moisturizer would suit me best?

I have oily skin and my budget is ₹700. Suggest products I can buy.

Recommend the best shampoos within my budget.

The system interprets the user's requirements and evaluates relevantproducts using product information, historical customer-review signals,ratings, review counts, and the ML ranking score before generatingrecommendations.

⚖️ Product Comparison

Users can ask questions such as:

Compare CeraVe and Cetaphil moisturizers.

The comparison workflow uses the LLM to provide a conversationalcomparison rather than simply returning raw database records.

💡 Product Information

The assistant can also answer general beauty and skincare questions, forexample:

What is niacinamide?

Which type of moisturizer is suitable for dry skin?

These information-oriented questions can be answered directly by the LLMwithout unnecessarily passing through the recommendation pipeline.

🏗️ System Architecture



High-Level Flow

                        USER
                          │
                          ▼
                  React Frontend
                          │
                          ▼
                    FastAPI /chat
                          │
                          ▼
                Groq Llama 3.3 70B
                 Intent Extraction
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        Recommend      Compare    Information
             │            │            │
             ▼            ▼            ▼
      MongoDB Atlas      Llama        Llama
             │         Comparison    Response
             ▼
     Candidate Products
             │
             ▼
          XGBoost
       Product Ranking
             │
             ▼
      Llama Reasoning
             │
             ▼
   Personalized Recommendations

🔧 Technology Stack

Layer                   Technology              Purpose

LLM                     Groq Llama 3.3 70B      Intent understanding,reasoning and responsegeneration

ML                      XGBoost                 Product scoring andranking

Backend                 FastAPI                 API and workfloworchestration

Database                MongoDB Atlas           Product and historicaldata storage

Frontend                React                   Conversational UI

API Client              Axios                   Frontend-backendcommunication

📊 Role of XGBoost

XGBoost acts as the data-driven ranking layer of the recommendationpipeline.

Candidate products are passed through the trained model and assigned anML score based on the features used during model training.

The score is then used to rank candidate products before the LLMperforms its final contextual reasoning.

Candidate Products
        ↓
     XGBoost
        ↓
     ML Score
        ↓
   Product Ranking
        ↓
   LLM Reasoning
        ↓
Final Recommendations

The LLM is therefore not simply returning the highest-rated product, andXGBoost is not independently making the final decision. The twocomponents complement each other.

🗄️ Dataset

The project uses the Amazon Beauty dataset containing product-levelinformation and historical customer-review signals.

The data includes fields such as:

Product title

Brand

Category

Price

Average rating

Rating/review count

Product descriptions

Product features

Product images

The dataset is stored in MongoDB Atlas for application-levelretrieval.

The raw dataset is not included in this repository.

🔀 Intent Routing

The LLM extracts structured intent from the user's query and routes therequest to the appropriate workflow.

Supported intents:

recommend
compare
information

Recommendation

User Query
    ↓
Intent Extraction
    ↓
Candidate Retrieval
    ↓
XGBoost Ranking
    ↓
LLM Reasoning
    ↓
Recommendations

Comparison

User Query
    ↓
Intent Extraction
    ↓
LLM Comparison
    ↓
Comparison Response

Information

User Query
    ↓
Intent Extraction
    ↓
LLM
    ↓
Information Response

🔌 API

POST /chat

Main conversational endpoint.

Request

{
  "message": "Recommend a moisturizer under 700 for dry skin"
}

Recommendation Response

{
  "success": true,
  "type": "recommendation",
  "data": {
    "products": [
      {
        "id": "...",
        "asin": "...",
        "title": "...",
        "brand": "...",
        "category": "...",
        "price": 699,
        "average_rating": 4.7,
        "rating_number": 125,
        "image": "...",
        "features": [],
        "ml_score": 0.94,
        "ai_explanation": "..."
      }
    ]
  },
  "error": null
}

Interactive API documentation is available through FastAPI Swagger UI:

http://localhost:8000/docs

📁 Project Structure

agentic-ai-shopping-assistant/
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   │
│   ├── routers/
│   │   └── chat.py
│   │
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── mongodb_service.py
│   │   └── ml_service.py
│   │
│   └── models/
│       ├── model.joblib
│       └── feature_columns.pkl
│
├── frontend/
│   ├── package.json
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/
│       ├── types/
│       ├── App.*
│       └── main.*
│
├── docs/
│   └── architecture.png
│
├── .env.example
├── .gitignore
├── README.md
└── LICENSE

⚙️ Setup

1. Clone the repository

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd agentic-ai-shopping-assistant

2. Create a Python virtual environment

python -m venv .venv

Activate it on Windows:

.venv\Scripts\activate

Activate it on macOS/Linux:

source .venv/bin/activate

3. Install backend dependencies

cd backend
pip install -r requirements.txt

4. Configure environment variables

Create a .env file based on .env.example.

GROQ_API_KEY=your_groq_api_key
MONGODB_URI=your_mongodb_connection_string
DATABASE_NAME=your_database_name
VITE_API_URL=http://localhost:8000

Never commit the actual .env file to GitHub.

5. Start the backend

From the backend directory:

uvicorn main:app --reload

The API will be available at:

http://localhost:8000

Swagger documentation:

http://localhost:8000/docs

6. Start the frontend

Open another terminal:

cd frontend
npm install
npm run dev

The frontend will be available at the URL shown by Vite.

🔐 Environment Variables

Variable          Description

GROQ_API_KEY    Groq API keyMONGODB_URI     MongoDB Atlas connection stringDATABASE_NAME   MongoDB database nameVITE_API_URL    FastAPI backend URL

🧪 Example Queries

Recommend a moisturizer under ₹700 for dry skin.

I have oily skin. Which moisturizer would suit me?

Suggest shampoos within my budget.

Compare CeraVe and Cetaphil moisturizers.

What is niacinamide?

What skincare products are suitable for sensitive skin?

💡 Key Learning & Insights

One of the biggest takeaways from this project was understanding that aneffective AI shopping assistant does not need to rely entirely on anLLM.

Different components can complement one another:

MongoDB Atlas provides product and historical data.

XGBoost provides a data-driven ranking signal.

Llama understands natural language and performs contextualreasoning.

FastAPI orchestrates the workflows.

React turns the system into an interactive application.

During development, the recommendation pipeline also highlighted theimportance of candidate retrieval. A ranking model can only rank theproducts it receives, so the retrieval stage must respect the user'sactual product intent before ML ranking takes place.

This helped shape the final architecture into a combination of:

User Intent + Historical Signals + ML Ranking + LLM Reasoning

rather than simply:

Keyword Search + Highest-Rated Product

🚀 Future Enhancements

Potential improvements include:

🔎 Semantic/vector search for more context-aware retrieval

🧠 Long-term conversational memory

🎯 More personalized recommendation features

📈 Expanded recommendation evaluation and ranking metrics

🔄 Real-time product availability and pricing

🛒 E-commerce purchasing/affiliate integration

📱 Further frontend and UX improvements

☁️ Production deployment and cloud optimization
