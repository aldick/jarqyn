# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory to match the project structure expected by main.py
# main.py does: Path(__file__).resolve().parent.parent.parent
# If main.py is in /Jarqyn/backend/app/main.py, then parent.parent.parent is /Jarqyn
WORKDIR /Jarqyn/backend

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
