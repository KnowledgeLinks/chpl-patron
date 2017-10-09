# Dockerfile for Chapel Hills Public Library Patron Registration
FROM python:3.6.3
MAINTAINER Jeremy Nelson <jermnelson@gmail.com>

ENV HOME /opt/chpl-patron
RUN apt-get update && mkdir -p $HOME && mkdir $HOME/instance
COPY db-schema.sql $HOME
COPY instance/config.py $HOME/instance/config.py
COPY iii $HOME/iii
COPY postalcodes $HOME/postalcodes
COPY registration.py $HOME
COPY requirements.txt $HOME
RUN cd $HOME && pip install -r requirements.txt
    
WORKDIR $HOME
CMD ["nohup", "gunicorn", "-b", "0.0.0.0:3000", "registration:app"]
