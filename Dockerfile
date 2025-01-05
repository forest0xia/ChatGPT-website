# Start from a lightweight Python image
FROM python:3.9-slim

# Create a directory to hold your code in the container
WORKDIR /app

# Copy and install dependencies first for efficient layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of your application
COPY . .

# Let Cloud Run set the port; default to 8080 if not set
ENV PORT 8080

# For production, use Gunicorn as the process manager:
#   - "app:app" means "import app (app.py) and run the Flask 'app' object"
#   - Bind to 0.0.0.0:$PORT so Cloud Run can route traffic
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 1
