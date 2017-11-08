# Simple FBA(Federated Byzantine Agreement) Implementation

## Premise

* one ledger(block) has one transaction
* sibling(s) means the nodes in the same quorum
* slot has one ballot, and one ballot has one transaction
* to make story simple and easy, the keypair of stellar will be used


## Consensus Process

### Start Node

1. check latest transaction id from storage
    1. compare between local transaction id and siblings
    1. if different
    1. catchup
1. catched up


### New Transaction Received

1. validate transaction
    1. if it is not valid, response error(`401`)
1. check the ballot is opened or not
    1. if opened, wait until the ballot is closed
        1. the received transaction goes to the transaction pool
    1. if closed,
        1. check the siblings ballot is opened or not
            1. if opened ballot is found,
                1. check the transaction in ballot is already handled in current node or not
                    1. if it is already handled, skip it
                    1. if not,
                        1. open new ballot with that ballot
                1. wait until the ballot is closed
            1. if not found,
                1. pass
1. start new ballot with new transaction


### New Ballot Is Created

1. broadcast the ballot to siblings
1. if all nodes accept new ballot
    1. start consensus process
1. if not,
    1. if another nodes has the opened ballot with previous transaction id
        1. wait until that ballot is closed


### Start Agreement, Consensus Process

1. receive the result of validation of other (known) siblings in the same quorum
1. if the count of accepted is over threshold,
    1. broadcast closing ballot signal to the siblings
1. got close signal
    1. save the transaction in ballot to the storage


### When Node Started

1. if node is new,
    1. create new storage
    1. create genesis account
1. start network with given port
1. if possible, trying to find siblings in the same quorum


## Installation

* Python 3.6.x or higher
* nothging :)

### Linux
```
$ apt install python3 python3-pip
$ pip3 install virtualenv
```


### OSX
```
$ brew install python3
$ pip install virtualenv
```


### Source

```
$ virtualenv ./simple-fba
Using base prefix '/usr'
New python executable in /root/simple-fba/bin/python3
Also creating executable in /root/simple-fba/bin/python
Installing setuptools, pip, wheel...cdone.
$ cd simple-fba
$ mkdir src
$ cd src
$ git clone https://github.com/spikeekips/simple-fba
```

```
$ python setup.py develop
```


## Run Nodes

For example, we will run 6 nodes with the different port in the same machine.

```
$ simple-fba-node.py -init -name=node0 -port=5000 -siblings=localhost:5001,localhost:5002,localhost:5003,localhost:5004,localhost:5005
$ simple-fba-node.py -init -name=node1 -port=5001 -siblings=localhost:5000,localhost:5002,localhost:5003,localhost:5004,localhost:5005
$ simple-fba-node.py -init -name=node2 -port=5002 -siblings=localhost:5001,localhost:5000,localhost:5003,localhost:5004,localhost:5005
$ simple-fba-node.py -init -name=node3 -port=5003 -siblings=localhost:5001,localhost:5002,localhost:5000,localhost:5004,localhost:5005
$ simple-fba-node.py -init -name=node4 -port=5004 -siblings=localhost:5001,localhost:5002,localhost:5003,localhost:5000,localhost:5005
$ simple-fba-node.py -init -name=node5 -port=5005 -siblings=localhost:5001,localhost:5002,localhost:5003,localhost:5004,localhost:5000
```

and then, send the 100 payment to the `node0` node. At first, the client or wallet needs it's own secret seed. To generate secret seed, visit https://portal.willet.io .
```
$ simple-fba-wallet.py node0 SCQ2IRPN4OXFIZNZODN6JQF6O4F2Z3ODA4W27C2GQSVD5WK2KQNA6WKF GAFVNM4NQLCE2RLQLYHIOIZAUEDG4U7RTGRTVNMKFX6KF3QKXTW72ULP 100
```

`GAFVNM4NQLCE2RLQLYHIOIZAUEDG4U7RTGRTVNMKFX6KF3QKXTW72ULP` is the public address of the other account.


## TODO

* Generating keypair
* Creating account
