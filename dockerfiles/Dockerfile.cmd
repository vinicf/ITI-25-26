# Use Ubuntu 24.04 as the base
FROM ubuntu:24.04

# Set ENV to avoid interactive prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Update apt and install python3-pip
RUN apt-get update && apt-get install -y python3.12-venv python3-pip

# Set a working directory inside the container
WORKDIR /app

# Copy the requirements and app files into the container
COPY ./um_drive/ ./

# create a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the Python dependencies
RUN pip install -r requirements.txt

# Set the default command to run when the container starts
CMD ["python3", "app.py"]
