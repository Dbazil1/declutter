# Declutter

A Streamlit application for managing and selling household items.

## Features
- Item management with images
- Price tracking
- WhatsApp message formatting
- Family collaboration (coming soon)

## Setup
1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Supabase credentials:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

4. Set up the database:
   - Go to your Supabase project dashboard
   - Open the SQL Editor
   - Run the `database_setup.sql` script to create tables and policies
   - Run the `functions.sql` script to create database functions

5. Run the application:
```bash
streamlit run app.py
```

## Development
This project uses:
- Streamlit for the web interface
- Supabase for backend services
- Python 3.11+