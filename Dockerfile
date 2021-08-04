# pull official base image
FROM ubuntu:latest

# set work directory
WORKDIR /usr/src/clustering_mvp

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

USER root

# install dependencies
COPY ./requirements.txt .
RUN apt -y update
RUN apt install -y python3-pip
RUN apt install -y python3.9
RUN apt install -y make automake gcc g++ subversion python3-dev libc-dev build-essential
RUN pip3 install --upgrade pip
RUN python3.9 -m pip install -U --no-cache-dir -r requirements.txt
#RUN pip3 install -r requirements.txt

# copy project
COPY . .
CMD ["python3.9", "./manage.py", "makemigrations"]
CMD ["python3.9", "./manage.py", "migrate"]
EXPOSE 8080
CMD ["python3.9", "./manage.py",  "runserver", "0.0.0.0:8080"]
