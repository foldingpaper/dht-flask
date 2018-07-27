import logging
import random
import sha
import sys
from flask import Flask, request, redirect

logger = logging.getLogger('dht')
logger.setLevel(logging.DEBUG)


#
# key/unique id size in number of bits
#
NUM_KEY_BITS = 40


#
# This node's kv table
#
table = {}


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
  """
  Something analogous to --help on typical command line tools.
  """
  return ('
    GET /ht/<key>\r\n
    POST /ht/<key> with <value> as body content-type:text/plain\r\n
    DELETE /ht/<key>\r\n
    POST /dht/join with name,id,address as url-encoded-form\r\n
    POST /dht/leave with name,id,address as url-encoded-form\r\n
  ')


@app.route('/keys', methods=['GET'])
def keys():
  """
  Returns all keys on this node:

  <key1>\r\n<key2>\r\n...
  """
  return "Keys on this node: %s" % table.keys()


@app.route('/ht/<key>', methods=['GET'])
def get(key):
  """
  Returns the value for the key stored in this DHT or an empty
  if key maps to this node. If key maps to different node, then
  redirects to that other node.
  """
  val = lookup(my_index, key)
  return val if val else ''


@app.route('/ht/<key>', methods=['POST', 'PUT'])
def put(key):
  """
  Upserts the key into the DHT. The value is equal to the body of the HTTP
  request.
  If key maps to different node, then redirects to that other node.
  """
  store(my_index, key, request.data)
  return "Added table[%s] = %s" % (key, request.data)


@app.route('/ht/<key>', methods=['DELETE'])
def delete(key):
  """
  Deletes the key from the DHT if it exists, noop otherwise.
  """
  delete(my_index, key)
  return "Deleted table[%s]" % key
  raise NotImplemented


@app.route('/dht/members', methods=['GET'])
def members():
  """
  list of members
  a carriage return and a new line:

    <member1>\r\n<member2>\r\n
  """
  return "Node Ids: %s\n" % nodes


@app.route('/dht/join', methods=['POST', 'PUT'])
def join():
  """
  Join a new node.

  A url-encoded form post e.g.

  address=http://127.0.0.1:5000&id:<theid>&name:<friendlyname>
  """
  logger.debug("before %s\n" % nodes)
  name = request.values['name']
  address = request.values['address']
  id = int(request.values['id'])
  add_node(id, address, name)
  return "Nodes %s\n" % nodes


@app.route('/dht/leave', methods=['GET'])
def leave():
  """
  Leave the current DHT.
  """
  raise NotImplemented


def add_node(id, address, name):
  """
  Add node to the federation.
  """
  global my_index
  global my_id

  info = {"address": address, "name": name}
  nodes_info[id] = info
  nodes.append(id)
  nodes.sort()
  for idx, val in enumerate(nodes):
    logger.debug("idx: %d, val: %s" % (idx, val))
    if val == my_id:
      logger.debug("idx: %d, val: %s" % (idx, val))
      my_index = idx
      logger.debug("my index: %d" % my_index)
  logger.debug("my index: %d" % my_index)
  logger.debug(nodes)
    

#
# Very trivial peer node ring. TODO: refactor to Node object.
#
my_id = None
my_index = None
nodes = []
nodes_info = {}

def next_node(idx):
  if idx == len(nodes)-1:
     return 0
  else:
     return idx+1


def distance(a, b):
    """
    Clockwise distance

    Based on the globally defined key size in bits -- k.
    Max node id is 2 to the power of k.
    """
    if a==b:
        return 0
    elif a<b:
        return b-a;
    else:
        return (2**NUM_KEY_BITS)+(b-a);


def findNode(begin, key):
    """
    Traverse the ring to find the node that's
    the destination of the target key.
    """
    nkey=int(sha.new(key).hexdigest(),16)
    logger.debug("Begin %d, key %s, nkey %d\n" % (begin, key, nkey))
    i = begin
    next = next_node(i)
    while distance(nodes[i], nkey) > \
          distance(nodes[next], nkey):
        i = next
        next = next_node(i)
    return i


def lookup(start, key):
    """
    Find node and get the value for they key
    """
    i = findNode(start, key)
    id = nodes[i]
    logger.debug("node found %d, %s" % (i, id))
    if (id == my_id):
      return table[key]
    else:
      info = nodes_info[id]
      logger.debug(info)
      logger.debug(info['address'])
      return redirect("%s/%s" % (info['address'], key), code=302)


def store(start, key, value):
    """ 
    Find node and store the key-value
    """
    i = findNode(start, key)
    id = nodes[i]
    logger.debug("node found %d, %s" % (i, id))
    if (id == my_id):
      table[key]=value
    else:
      info = nodes_info[id]
      logger.debug(info)
      logger.debug(info['address'])
      return redirect("%s/%s" % (info['address'], key), code=302)


def delete(start, key):
    """
    Find the node and delete key-value
    """
    i = findNode(start, key)
    id = nodes[i]
    logger.debug("node found %d, %s" % (i, id))
    if (id == my_id):
      del table[key]
    else:
      info = nodes_info[id]
      logger.debug(info)
      logger.debug(info['address'])
      return redirect("%s/%s" % (info['address'], key), code=302)


if __name__ == '__main__':

   # TODO: use commandline args to get name, default to ip address

   # name = sys.argv[1]
   # nkey=int(sha.new(name).hexdigest(),16)

   id=int(random.uniform(0,2**NUM_KEY_BITS))
   logger.debug("My id: %s\n" % id)
   my_id = id
   add_node(id, "http://127.0.0.1:5000", name)
   app.config.from_pyfile("app.cfg")
   app.run()


