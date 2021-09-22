FROM python:3.8-slim

# Copy Python module
COPY ./client /usr/src/app/client/

# Install dependencies
COPY ./requirements.txt /usr/src/app/
WORKDIR /usr/src/app/
RUN pip install --no-cache-dir -r /usr/src/listener/requirements.txt

# Run the application
CMD cd /usr/src/app/ && python3 -m client
