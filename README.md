# Shp to routable graph draft
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
wget http://download.neo4j.org/artifact?edition=community&version=3.4.7&distribution=tarball

tar -xzvf artifact.php?name=neo4j-community-3.4.7-unix.tar.gz

sudo mv neo4j-community-3.4.7 /etc

cd /etc/neo4j-community-3.4.7

sudo nano conf/neo4j.conf

# uncomment this line in the neo4j conf file
dbms.connectors.default_listen_address=0.0.0.0

./bin/neo4j start

cd /vagrant
```

