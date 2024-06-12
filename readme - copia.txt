# SpaceLink Simulator

## Description

The SpaceLink Simulator is a tool designed to simulate communication between a satellite and ground stations. The program calculates distances and transmission latencies, determining if the ground node is within the satellite's coverage and simulating the process of sending and receiving packets.

## Files

1. **Satellite1_130_10sec.csv**: Satellite path data for 30 days. Includes satellite positions at 10-second intervals.
2. **nodo_tierra.csv**: Ground node coordinates.
3. **ksat_ground_stations.csv**: Coordinates of the ground stations.

## Installation

To run this project, make sure you have Python 3 installed along with the following libraries:

- pandas
- numpy

You can install these dependencies using pip:

```bash
pip install pandas numpy
