# Simple FBA Implementation and Simulation

The FBA(Federated Byzantine Agreement) consensus protocol is the way to make agreement between untrusted network nodes. The well-known implementation of FBA in real world is the stellar blockchain network, which has the derived consensus, they called 'SCP'(Stellar Consensus Protocol).

This implementation will help to understand how the agreement is made in FBA and you can simply adjust the quorum size and threshold. Most of the concept and names was derived from SCP and FBA traditions. The more detailed information about FBA and SCP, you can simple find at the https://stellar.org and google. :)


## Installation

At first, install it.
```
$ virtualenv simple-fba
$ cd simple-fba
$ source bin/activate

$ git clone git@github.com:spikeekips/simple-fba.git src/simple-fba
$ cd src/simple-fba
$ python setup.py develop
```

Done!

## Run

Simple usage

```
$ simple-fba-simulator.py -h
usage: simple-fba-simulator.py [-h] [-s] [-nodes NODES] [-trs TRS]

optional arguments:
  -h, --help    show this help message and exit
  -s            turn off the debug messages
  -nodes NODES  number of validator nodes in the same quorum; default 4
  -trs TRS      threshold; 0 < trs <= 100
```

Run
```
$ simple-fba-simulator.py -s
```

> You can omit the `-s` option, you will see the more detailed debug messages.


The number of nodes(validators) can be set, by default, 4.
```
$ simple-fba-simulator.py -s -nodes 10
```

And 'threshold' value also can be set
```
$ simple-fba-simulator.py -s -nodes 10 -trs 60
```
