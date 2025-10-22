#!/bin/bash
# Setup script for Streamlit Cloud deployment

echo "Setting up database..."

# Check if database exists
if [ ! -f "pe_portfolio.db" ]; then
    echo "Database not found. Running import script..."
    python import_to_database.py
else
    echo "Database already exists."
fi

echo "Setup complete!"
