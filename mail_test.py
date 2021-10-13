# from flask import Flask
# from flask_mail import Mail
# import smtplib
# import email.utils
# from email.mime.text import MIMEText
# app = Flask(__name__)
# mail = Mail(app)

# from flask_mail import Message

# @app.route("/")
# def index():

#     msg = Message("Hello",
#                   sender="michael.stabile@socom.mil",
#                   recipients=["mstabile75@gmail.com"])
#     mail.send(msg)
#     return "<h1>Msg sent</h1>"


# msg = MIMEText('This is the body of the message.')
# msg['To'] = email.utils.formataddr(('Recipient', 'mstabile75@gmail.com'))
# msg['From'] = email.utils.formataddr(('Author', 'mstabile75@gmail.com'))
# msg['Subject'] = 'Simple test message'

# server = smtplib.SMTP('localhost')
# server.set_debuglevel(True) # show communication with the server
# try:
#     server.sendmail('mstabile75@gmail.com', ['mstabile75@gmail.com'], msg.as_string())
# finally:
#     server.quit()

#if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=4000, debug=True)
    # msg = MIMEText("test messge")
    # msg['Subject'] = "New Card Request"
    # msg['From'] = "michael.stabile@socom.mil" 
    # msg['To'] = "mstabile75@gmail.com"
    # mail_server = smtplib.SMTP('localhost',port=1025)
    # mail_server.send_message(msg)
    # mail_server.quit()
    # Create the message

import sys
import smtplib
import dns.resolver

email = "mstabile75@gmail.com"
url = email.split("@")[1]


answers = dns.resolver.query(url, 'MX')
if len(answers) <= 0:
    sys.stderr.write('No mail servers found for destination\n')
    sys.exit(1)
 
# Just pick the first answer
server = str(answers[0].exchange)
 
# Add the From: and To: headers
fromaddr = 'source-email@whatever.com'
toaddr = email
body = 'some email body'
msg = "From: {}\r\nTo: {}\r\n\r\n{}".format(fromaddr, toaddr, body)
 
server = smtplib.SMTP(server)
server.set_debuglevel(1)
server.sendmail(fromaddr, toaddr, msg)
server.quit()

