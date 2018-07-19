# CATALOG

This application provides a list of items. Registered users can post, edit and delete their own items.

## PREREQUISITES

You'll need to install the following softwares to run the application:

- [Git](https://git-scm.com/downloads)
- [VirtualBox](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1)
- [Vagrant](https://www.vagrantup.com/downloads.html)

## RUN THE APPLICATION

To run your virtual machine (VM) open Git Bash in the app folder and type **vagrant up**, then type **vagrant ssh**.\
Type **cd /vagrant** to access the shared folder between your host machine and the VM.\
If it is the first time you run the application, type **python populate_db.py** to create the database and some default item.\
Type python **application.py** to run the application.


## USE THE APPLICATION

To have access to all of the functionalities of the app, visit [http://localhost:8000](http://localhost:8000).\
To access the JSON endpoint of an item, visit http://localhost:8000/catalog/ITEM_NAME/JSON.