# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code

# Install system dependencies
RUN apt-get update \
&& apt-get -y install netcat-openbsd gcc \
&& apt-get clean

# Install Python dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Add the rest of the code
COPY . /code/

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Command to run the application
WORKDIR /code/vlp

# run collectstatic
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "server.wsgi:application"]
