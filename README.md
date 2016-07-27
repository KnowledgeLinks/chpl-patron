[FLSK]: http://flask.pocoo.org/
[INFLUX]: http://wearefinflux.com/

# CHPL Patron Registration
This [Flask][FLSK] application provides the middleware processing of Patron
self-registration for Chapel-Hill Public Library's Wordpress website 
created by Aaron Schmidt of [Influx Design][INFLUX].

## Set-up
Clone repository with git `git clone https://github.com/KnowledgeLinks/chpl-patron.git`.. 

Create a `instance` directory in the chpl-patron directory and a `config.py` that has 
the following variables set:

    SIERRA_URL = "{url to III's Sierra self-registration form}"

    EMAIL_SENDER = Sender's email address

    EMAIL_RECIPIENTS = List of receipients for notification emails

    SUCCESS_URI = Redirect URL to a Wordpress Page for a successful registration

    ERROR_URI = Redirect URL to a Wordpress Page for a failed registration

Install Python 3.5 dependencies using `pip3 install -r requirements.txt`.
 
## Development
Running in development by `python3 registration.py` using the built-in development
Flask server with debug turned on and accessible on port 5000.

## Production
Use [gunicorn](http://gunicorn.org/) to run as a Python WSGI HTTP server on Linux 
or Mac with this command `nohup gunicorn -w 2 -b :4000 registration:app &` to run in the 
background with two threads on port 4000. 
