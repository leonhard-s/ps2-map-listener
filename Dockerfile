FROM python:3.8-slim

# Copy Python module
COPY ./apl_listener /usr/src/listener/

# Install dependencies
COPY ./requirements.txt /usr/src/listener/
RUN pip install --no-cache-dir -r /usr/src/listener/requirements.txt

# Update working directory
WORKDIR /usr/src/listener/

# Run the application
CMD ["python3", "-m", "apl_listener"]
