manul_bot/
├── config/                # Configuration templates and group rules
├── core/                  # Core Business Logic & Infrastructure
│   ├── database/          # SQL Repositories (Customer, User tables)
│   ├── setup/             # Database initialization engine
│   ├── ai_clients.py      # Core LLM API integrations (Gemini, Groq)
│   ├── apify_client.py    # Scraping integration client
│   ├── auth_service.py    # Role-based access control (RBAC)
│   ├── customer_service.py# Business validation & data orchestration
│   ├── security.py        # AES-256 data encryption/decryption
│   └── utils.py           # Shared core utilities
├── handlers/              # Telegram State Machines (ConversationHandlers)
│   ├── admin_handlers.py  # Employee registration & admin setups
│   ├── vehicle_handlers.py# Vehicle intake & customer workflows
│   └── post_handlers.py   # AI Marketing post flows
├── keyboards/             # Telegram UI Elements
│   ├── reply_keyboards.py # Main persistent application menus
│   └── inline_keyboards.py# Dynamic contextual buttons
├── schema/                # PostgreSQL Sequential Migration Schemas
├── scripts/               # Maintenance, scraping (hunter.py) & database engines
├── services/              # Domain Services (Lead Hunter & AI scraping logic)
├── tests/                 # Automated test suites for AI & Bot behavior
├── uploads/               # Temporary and permanent storage for media/documents
└── utils/                 # General helpers (image processing, etc.)