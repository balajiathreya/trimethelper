from flask import Flask
from flask.ext.mail import Mail
from datetime import datetime
from flask_mail import Message
import urllib, time, pytz
import urllib2, base64
import credentials, json



MAIL_SERVER = credentials.MAIL_SERVER
MAIL_PORT = credentials.MAIL_PORT
MAIL_USE_TLS = credentials.MAIL_USE_TLS
MAIL_USE_SSL =  credentials.MAIL_USE_SSL
MAIL_USERNAME = credentials.MAIL_USERNAME
MAIL_PASSWORD = credentials.MAIL_PASSWORD

app = Flask(__name__)
app.config.from_object(__name__)
mail = Mail(app)


#https://dev.twitter.com/docs/auth/application-only-auth

@app.route("/checktrimetstatus")
def checktrimetstatus():
    bearerToken = getBearerToken()
    authorization = 'Bearer ' + bearerToken
    headers = {'Authorization':authorization}
    url = 'https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=trimet'

    #response = urllib2.urlopen("http://example.com/foo/bar").read()
    req = urllib2.Request(url, None, headers)
    response = urllib2.urlopen(req)
    data = response.read()   
    problems =  checkForProblems(data)
    sendEmail(problems)
    return '<br/>'.join(problems)


def checkForProblems(data):
    tweetsJSON = json.loads(data)
    problems = []
    delayFound = False;
    for tweet in tweetsJSON:
        text = tweet['text']
        created_at_utc  = pytz.utc.localize(datetime.strptime(tweet['created_at'].replace('+0000 ',''), '%a %b %d %H:%M:%S %Y'))
        created_at = created_at_utc.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Pacific'))
        now = datetime.now(pytz.timezone('US/Pacific'))
        diff_seconds = (now - created_at).seconds
        # difference is less than 3 hours
        if(diff_seconds < 10800):
            if(text.find('delay') != -1 or text.find('close') != -1):
                problems.append('At : ' + str(created_at.hour) + ':' + str(created_at.minute) +  ', ' + text)
    return problems;


def sendEmail(problems):
     msg = Message("Trimet problems",
                  sender=MAIL_USERNAME,
                  recipients=["athreya86@gmail.com"])
     msg.html = '<br/>'.join(problems)
     mail.send(msg)

def getBearerToken():
    return credentials.bearertoken


# bearer tokens don't change for now - but they may change in the future
def getBearerTokenFromTwitter():
    # construct header first
    basic = base64.b64encode(urllib.quote_plus(credentials.apikey) + ':' + urllib.quote_plus(credentials.apisecret))
    authorization = 'Basic ' + basic
    contentType = 'application/x-www-form-urlencoded;charset=UTF-8'
    headers = {'Authorization':authorization, 'Content-Type':contentType}
    # body then and make request
    body = 'grant_type=client_credentials'
    url = 'https://api.twitter.com/oauth2/token'
    req = urllib2.Request(url, body, headers)
    response = urllib2.urlopen(req)
    tokenJSON = json.loads(response.read())
    return tokenJSON['access_token']


if __name__ == "__main__":
    app.run(debug=True)
