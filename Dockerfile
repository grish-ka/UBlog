# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code (including your src folder)
COPY . .

# Create the instance directory inside src so SQLite has a place to live
RUN mkdir -p src/instance

# Expose port 5000
EXPOSE 5000

# Tell gunicorn to change into the 'src' directory before running the app
CMD ["gunicorn", "--chdir", "src", "--bind", "0.0.0.0:5000", "app:app"]