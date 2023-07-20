# Cisco SDWAN Ops GUI
Web GUI for basic SDWAN operations tasks.  Currently supports:
- Deploy a New Edge
- Change Edge Template Values
- RMA an Edge (Hardware Replacement)
- List Edges
- List Templates

Runs as a Python3 Flask app natively for testing.  Tested on GCP and Apache for production.

# Screenshots
### Menu Screenshot:

![ScreenShotMenu](https://user-images.githubusercontent.com/46031546/136583237-13c45f5c-7266-48e6-bea4-d2fd7b7e096e.png)

### Edit or Deploy a Device Screenshot:

![ScreenShotEdit](https://user-images.githubusercontent.com/46031546/136489454-385b339a-b5b6-46ac-be81-7153ce7eb8e7.png)

# Basic use instructions:
- Clone repository

    `git clone https://github.com/dbrown92700/vManagerGUI`
- Change to directory and create a virtual environment

    `cd vManagerGUI`
    
    `python3 -m venv env`
    
    `source env/bin/activate`
- Install python libraries

    `pip install -r requirements.txt`
- Execute the app

    `python3 main.py`
- Browse to the local webserver

    `http://localhost:8080`

# Apache Webserver Installation

- Install Apache if necessary.  It's installed by default on Ubuntu.
- Clone repository into /var/www
> sudo git clone ...
- Change to /var/www/vManagerGUI directory
> cd /var/www/vManagerGUI
- Create venv in /var/www/vManagerGUI
> sudo python3 -m venv venv
- Activate venv
> sudo source venv/bin/activate
- Install python packages
> sudo pip install -r requirements.txt
- Link WSGI and Apache config files to the correct directories.  Default config for 
the website is to run on root at port 80. You will need to edit vmanager.apache.conf
in the apache directory if that isn't available.
> sudo ln -s apache/vmanager.wsgi \
> sudo ln -s /var/www/vManagerGUI/apache/vmanager.apache.conf /etc/apache2/sites-available/
- Disable the default website and enable the new website
> sudo a2dissite 000-default.conf \
> sudo a2ensite vmanager.apache.conf
- Create .env file. Specify the certificate if needed for a secure connection. Local mysql
does not require SSL.
> sudo nano .env

SQLHOST=localhost \
SQLUSER=username \
SQLPASS=password \
DATABASE=vmanager \
SQLCERT=/etc/ssl/cert.pem

- Restart Apache
> sudo systemctl reload apache2.service

This project was written and is maintained by the following individuals:

## Author

* David Brown <davibrow@cisco.com>

