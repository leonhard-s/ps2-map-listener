FROM python:3.8-slim

# Copy Python module
COPY ./apl_listener /usr/src/listener/apl_listener/

# Install dependencies
COPY ./requirements.txt /usr/src/listener/
WORKDIR /usr/src/listener/
RUN pip install --no-cache-dir -r /usr/src/listener/requirements.txt

# Run the application
CMD cd /usr/src/listener/ && python3 -m apl_listener
