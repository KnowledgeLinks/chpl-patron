address checker 
https://chapelhillpubliclibrary.org/patroncheck/

API documentation 
https://sandbox.iii.com/iii/sierra-api/swagger/index.html#!/patrons/Create_a_patron_record_post_0

Chapel hill python scrip: https://github.com/townofchapelhill/chccs-post-update

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

    DUPLICATE_EMAIL_CHECK = Set to 'True' to disallow duplicate email registrations


Install Python 3.5 dependencies using `pip3 install -r requirements.txt`.
 
## Development
Running in development by `python3 chplpatron/registration/api.py` using the built-in development
Flask server with debug turned on and accessible on port 5000.

## Production
Use [gunicorn](http://gunicorn.org/) to run as a Python WSGI HTTP server on Linux 
or Mac with this command `sudo nohup gunicorn -w2 --certfile=instance/chapelhillpubliclibrary_org.crt --keyfile=instance/private_key.txt -b :8443 --log-file gunicorn.log --log-level INFO --timeout 90 chplpatron.registration.api:app &
` to run in the 
background with two threads on port 8443. 
