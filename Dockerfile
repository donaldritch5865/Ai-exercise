# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the Streamlit app dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port on which the Streamlit app will run
EXPOSE 8501

# Define the command to run your app
CMD ["streamlit", "run", "app.py"]
