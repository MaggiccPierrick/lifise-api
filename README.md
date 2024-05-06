# MetaBank API

The open Neo Bank powered by web3 for everyone.  
This repository is for the backend (API) of the solution including database management, object storage and webservices.  

See the following instructions to setup the MetaBank API on Ubuntu server.  

## 1. Setup server (Ubuntu 22)
#### Change ssh port
Update ssh config file to set new port and restart ssh  
```
sudo nano /etc/ssh/sshd_config
sudo service ssh restart
```

Configure and enable firewall
```
sudo ufw allow 12345  
sudo ufw enable
```

#### Create dedicated local user
Create the user  
``` adduser codinsight ```

Add the newly created user as a sudoer  
``` usermod -aG sudo codinsight ```

Allow the user to connect the server via ssh  
Copy / paste the authorized key from root user to codinsight user (as root)  
```
mkdir /home/codinsight/.ssh
cp /root/.ssh/authorized_keys /home/codinsight/.ssh/authorized_keys
cd /home/codinsight
chown codinsight:codinsight .ssh
cd .ssh
chown codinsight:codinsight authorized_keys
```

Disconnect and connect with the new user.  

#### Create ssh keys for gitlab CI/CD
Create gitlab deploy key without passphrase on the server in /home/codinsight/.ssh directory  
``` ssh-keygen -t rsa -b 4096 ```

Copy public key in gitlab here: https://gitlab.com/codinsight/metabank/metabank-api/-/settings/repository  
in "Deploy keys" section.  

Create ssh key (locally on laptop) for Gitlab CI/CD, without passphrase  
``` ssh-keygen -t rsa -b 4096 ```

Copy private key in Gitlab CI/CD variables here: https://gitlab.com/codinsight/metabank/metabank-api/-/settings/ci_cd  
in "Variables" section.  
Copy public key in authorized_keys file on the server (/home/codinsight/.ssh/authorized_keys)


#### Set CI/CD variables in Gitlab
METABANK_SANDBOX_URL: url of the server  
METABANK_SANDBOX_SSH_PORT: ssh port on the server  
METABANK_SANDBOX_SSH_PRIVATE_KEY: private key to access the server  
METABANK_SANDBOX_USERNAME: username of the operating system account  
METABANK_SANDBOX_SSH_KNOWN_HOSTS: copy / paste the content of the known_hosts (on your laptop) file created when connecting the server  


## 2. First installation of the project
#### Clone the repository
Add private key to ssh agent  
```
eval "$(ssh-agent -s)"
ssh-add /home/codinsight/.ssh/gitlab_deploy
```

Clone the repository using ssh  
```
git clone git@gitlab.com:codinsight/metabank/metabank-api.git
```

#### Install OS dependencies
```
sudo apt install Python3.10  
sudo apt install nginx  
sudo apt install python3-certbot-nginx  
sudo apt install pkg-config  
sudo apt install automake  
sudo apt install libtool  
sudo apt install make  
sudo apt install python3-pip
sudo apt install pipenv
```


#### Install and setup Redis
Download and install Redis
```
curl -s -o redis-stable.tar.gz http://download.redis.io/redis-stable.tar.gz
sudo tar -C /usr/local/lib/ -xzf redis-stable.tar.gz
rm redis-stable.tar.gz
cd /usr/local/lib/redis-stable/
sudo make
sudo make install
```

Verify Redis is in PATH and version number  
```
redis-cli --version
```

Create needed directories (verify that the owner of the directories is the application user (codinsight))  
```
sudo mkdir -p /etc/redis/metabank-api/
sudo chown codinsight:codinsight /etc/redis/metabank-api/
sudo mkdir /var/log/redis-metabank/
sudo chown codinsight:codinsight /var/log/redis-metabank/
sudo nano /etc/redis/metabank-api.conf
```

Copy / paste the following content in Redis config file (/etc/redis/metabank-api.conf)  
```
port              6379
daemonize         no
save              60 1
bind              127.0.0.1 ::1
tcp-keepalive     300
dbfilename        metabank-api.rdb
dir               /etc/redis/metabank-api/
rdbcompression    yes
supervised        systemd
pidfile           /var/run/redis-metabank-api.pid
loglevel          notice
logfile           /var/log/redis-metabank/metabank-api.log
```

Set Redis as a service by creating the Redis service file  
```
sudo nano /etc/systemd/system/redis-metabank-api.service
```

And copy / paste the following content  
```
[Unit]
Description=Redis In-Memory Data Store for MetaBank API
After=network.target

[Service]
User=codinsight
Group=codinsight
Type=notify
ExecStart=/usr/local/bin/redis-server /etc/redis/metabank-api.conf
ExecStop=/usr/local/bin/redis-cli shutdown
Restart=always

[Install]
WantedBy=multi-user.target
```

Allow Redis service to start at server boot as codinsight user  
```
systemctl enable redis-metabank-api.service
```


#### Setup virtual environment and install Python dependencies
```
pip3 install pipenv
cd /home/codinsight/metabank-api/
eval "$(ssh-agent -s)"
ssh-add /home/codinsight/.ssh/gitlab_deploy
git fetch
git checkout sandbox
pipenv install
```

#### Create local directories and files
```
nano conf/metabank-api.env              # and copy/paste and update content
mkdir var
mkdir var/log
nano var/metabank-sb-db.pem             # and copy/paste database certificate
```

#### Configure Nginx
Follow instructions here : https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uwsgi-and-nginx-on-ubuntu-22-04  
Create api.metabank.codinsight.app config file in /etc/nginx/sites-available with the following content.  
```
sudo nano /etc/nginx/sites-enabled/api.metabank.codinsight.app
```

```
server {
    listen 80;
    server_name api.metabank.codinsight.app www.api.api.metabank.codinsight.app;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/home/codinsight/metabank-api/metabank-api.sock;
    }
}
```

#### Add firewall rules for Nginx
```
sudo ufw allow 'Nginx HTTPS'  
sudo ufw allow 'Nginx HTTP'  
```

#### uWSGI

Test if uwsgi is working well  
```
pipenv shell
uwsgi --socket 0.0.0.0:14000 --protocol=http -w wsgi:app
```  

Create uwsgi log directory and metabank-api.log file  
```
sudo mkdir /var/log/uwsgi
sudo touch /var/log/uwsgi/metabank-api.log
sudo chown codinsight:codinsight /var/log/uwsgi/metabank-api.log
```

#### Run MetaBank API as a service
Create systemd service file  
```
sudo nano /etc/systemd/system/metabank-api.service
```  

And copy / paste the following content:  
```
[Unit]
Description=uWSGI instance to serve MetaBank API
After=network.target

[Service]
User=codinsight
Group=codinsight
WorkingDirectory=/home/codinsight/metabank-api
Environment="PATH=/home/codinsight/.local/share/virtualenvs/metabank-api-oFMDqNVs/bin"
ExecStart=/home/codinsight/.local/share/virtualenvs/metabank-api-oFMDqNVs/bin/uwsgi --ini metabank-api.ini

[Install]
WantedBy=multi-user.target
```

Allow MetaBank API service to start at server boot as codinsight user  
```
systemctl enable metabank-api.service
```

#### Allow the user to restart the service as sudoer without password  
Edit sudoer file  
```
sudo visudo
```

And add the following line  
```
codinsight ALL=(ALL) NOPASSWD: /bin/systemctl restart metabank-api.service
```

#### Add ssl certificate to Nginx
Activate Certbot, install ssl certificate and configure Nginx for the given domain  
```
sudo certbot --nginx -d api.metabank.codinsight.app -d www.api.metabank.codinsight.app
```  
NB: press 2 to activate automatic redirection from HTTP to HTTPS  

After this step, the Nginx config file should look like this (Add CORS if necessary) :  
```
sudo nano /etc/nginx/sites-enabled/api.metabank.codinsight.app
```

```
server {
    server_name api.metabank.codinsight.app www.api.metabank.codinsight.app;

    access_log /var/log/nginx/api.metabank.codinsight.access.log;
    error_log /var/log/nginx/api.metabank.codinsight.error.log;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/home/codinsight/metabank-api/metabank-api.sock;

        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '$http_origin';
            add_header 'Access-Control-Allow-Credentials' 'true';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, PATCH, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,X-AUTH-USER,X-API-KEY,X-API-SIGN';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain charset=UTF-8';
            add_header 'Content-Length' 0;
            return 204;
        }

        set $cors '';
        if ($http_origin ~ '^https?://(localhost|www\.app.metabank.codinsight.app)') {
            set $cors 'true';
        }

        if ($cors = 'true') {
            add_header 'Access-Control-Allow-Origin' "$http_origin" always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, PATCH, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Accept,Authorization,Cache-Control,Content-Type,DNT,If-Modified-Since,Keep-Alive,Origin,User-Agent,X-Requested-With,X-AUTH-USER,X-API-KEY,X-API-SIGN' always;
            # required to be able to read Authorization header in frontend
            # add_header 'Access-Control-Expose-Headers' 'Authorization' always;
        }
    }
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/api.metabank.codinsight.app/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/api.metabank.codinsight.app/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = api.metabank.codinsight.app) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name api.metabank.codinsight.app www.api.api.metabank.codinsight.app;
    return 404; # managed by Certbot
}
```

#### Auto renew certificate
(maybe not needed as Let's encrypt seems to add automatic rule to renew certificate ?)  
Add command line to crontab:  
```
crontab -e
```  
```
0 0 4 * * root certbot -q renew --nginx
```  
NB: useful link: https://crontab.guru/


## 3. Setup managed database
#### Add database SSL certificate in project var directory
```
nano metabank-sb-db.pem
```  
And copy / paste the content of the certificate  

##### Update config file according to the database settings
```
SQL_USER =
SQL_PASSWORD =
SQL_HOST =
SQL_PORT=
SQL_DB_NAME =
SQL_SSL_CERT =
```

#### Create database structure
Connect database using the following command (with admin user)
```
mysql -h 51.159.8.77 --port 14053 -p -u admin
```

And create all the tables (see db_structure.sql file in the repo)


## 4. Possible issues
#### Nginx failure : "failed (13: Permission denied) while connecting to upstream"
!!! From Ubuntu 22, Nginx does not have the rights to access the project directory in home folder.  
Solutions:  
- Change the group of the newly created user and his home directory to www-data  
```
sudo usermod -a -G www-data codinsight
sudo chgrp www-data /home/codinsight
sudo nano /etc/nginx/nginx.conf
```
OR  
- Change the user of the Nginx service to the local user  
```
sudo nano /etc/nginx/nginx.conf
```
Change Nginx user from www-data to codinsight and restart Nginx.  
