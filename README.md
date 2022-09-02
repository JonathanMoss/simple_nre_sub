# simple_nre_sub
A simple (Quick & Dirty) implementation of a connection to NRE Live Departure Boards for the purposes of evaluation and development

## Summary

In a nutshell, it spins up a RabbitMQ instance, connected to National Rail Enquiries, polls the NRE server every x seconds and places the results on the RabbitMQ exchange for consumption by whatever

## Environment Variables Needed
```bash
RMQ_USER          # Can be anything
RMQ_PASS          # Can be anything
CRS               # e.g. CRE,PAD,RDG (in CSV format, no spaces)
SLDB_TOKEN        # NRE Connection token supplied at registration
SLDB_WSDL         # Tested on: https://lite.realtime.nationalrail.co.uk/OpenLDBSVWS/wsdl.aspx?ver=2021-11-01
SLDB_FREQ         # The frequency in seconds to poll the results
SLDB_RMQ_EXCHANGE # Name of the RMQ exchange, can be anything
```

## Usage
```bash
$ cd simple_nre_sub
~/simple_nre_sub$ docker build -t base-python -f docker/base-python/Dockerfile .
~/simple_nre_sub$ docker-compose build
~/simple_nre_sub$ docker-compose up -d
```
