Fun Distributed Hash Table with REST API using Flask
====

A fun implementation of DHT as a learning exercise which in
turn helps me appreciate the design of various systems that
employ DHT in some form.

Requirements
----

* python
* flask
* virtualenv

Design
----

A simple design, each node in the group/federation has an
in-memory hash table. The data is distributed based on a
Chord-like design using consistent hashing to find the
appropriate node. The network group is formed using the
/ht/join api to be performed on every node. After identifying
the responsible node, we use HTTP redirect to bounce to the 
right node.


API
----

* POST /ht/<key> -d <value> -H "Content-Type: text/plain"
* GET /ht/<key>
* POST /ht/join -d "name=5001&address=http://127.0.0.1:5001/ht&id=1"

A Simple Sequence
----

1. Start two instances
```
python dht.py 6001
python dht.py 5001
```

2. Form the member group
```
curl -X POST http://127.0.0.1:6001/dht/join \
  -d "name=5001&address=http://127.0.0.1:5001/ht&id=1"
curl -X POST http://127.0.0.1:5001/dht/join \
  -d "name=6001&address=http://127.0.0.1:6001/ht&id=5"
```

3. Store data and retrieve, note the -L to follow redirects.
```
curl -X POST http://127.0.0.1:6001/ht/foo \
  -d bar -H "Content-Type: text/plain"
curl http://127.0.0.1:5001/ht/foo
curl -v http://127.0.0.1:5001/ht/foo -L
```

TODO
----

* improve to use command-line args for port, name, etc
* see if we can join using some known protocol/technique
* how to handle rebalancing
