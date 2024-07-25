# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and the Python script into the container
COPY hue_server.py /app/

# Install the required Python packages
RUN pip install phue

# Expose the port the server will run on
EXPOSE 8080

# Command to run the server
CMD ["python", "hue_server.py"]

