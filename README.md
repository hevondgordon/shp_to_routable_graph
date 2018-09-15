## Step 1 — Install vagrant
* Ensure that you have vagrant installed. [vagrant can be found here](https://www.vagrantup.com).
* After a successful installation of vagrant, run the following command from the project root:

```
vagrant up && vagrant ssh
```

## Step 2 — Setup virtual environment
* Install pip. `sudo apt install python3-pip`
* Install virtualenv. `sudo pip3 install virtualenv`
* Navigate to vagrant shared folder. `cd /vagrant`
* Create virtual environment. `virtualenv venv`
* Activate virtual environment. `. venv/bin/activate`
* Install requirements. `pip3 install -r requirements.txt`

## Step 3 — Install Neo4j
* Install java. `sudo apt-get install openjdk-8-jre-headless`
* Install neo4j 
```
wget -O - https://debian.neo4j.org/neotechnology.gpg.key | sudo apt-key add -

echo 'deb https://debian.neo4j.org/repo stable/' | sudo tee -a /etc/apt/sources.list.d/neo4j.list

sudo apt-get update

sudo apt-get install neo4j=1:3.4.7
```

* Update Neo4j config to listen on global interface.

```
cd /etc/neo4j/

sudo nano neo4j.conf

#uncomment the following line 
dbms.connectors.default_listen_address=0.0.0.0
```