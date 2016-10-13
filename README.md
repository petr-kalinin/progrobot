# About
This bot can send you reference of programming language elements. For example, you can send it message `vector insert`, and it will send you the reference for C++'s `std::vector::insert()`. Currently, C++ and Python are supported.

# Setting up
## Prerequisites

You need to have Python 3 and mongodb installed.

Install some python packages:

    sudo pip3 install pymongo
    sudo pip3 install bs4
    sudo pip3 install lxml

## Import reference

All the commands below are relative to the directory of bot's source code.

Create direcory `raw_data` and download the reference files from docs.python.org and from cppreference.com. Namely, for Python I use the following command:

    mkdir raw_data/python3; cd raw_data/python3; wget -r -np https://docs.python.org/3/library/
    
For cppreference, download the offline version ("HTML book") from http://en.cppreference.com/w/Cppreference:Archives and unzip it to `raw_data/cpp`.

As a result, you should have, for example, the following files:

    raw_data/cpp/reference/en/cpp/algorithm/accumulate.html
    raw_data/python3/docs.python.org/3/library/2to3.html
    
(the `docs.python.org` is created by `wget`).

Make sure you have mongodb server running on localhost with default parameters. Alternatively, you can run `mkdir data; ./mongo.sh` to start a local copy of mongo server. If you want to use mongodb server with non-default parameters or a non-localhost server, you can edit `main.py` where `pymongo.MongoClient()` is created, and similarly edit `tools/import_*.py` files.

Now run the following command to import the reference to mongo databases:

    cd tools; ./import_cppref.py; ./import_python.py

(this may take some time).

TBD

Please note that I license the bot under the GNU Affero General Public License. This means that if you make changes to it and open the changed bot to public, you must disclose your source code.
