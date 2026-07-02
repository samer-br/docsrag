# Atlas-7 Picking Robot — Product Specification

## Overview

The Atlas-7 is Northwind Robotics' autonomous picking robot for warehouse
fulfilment. It navigates aisles, locates items, and delivers them to packing
stations without fixed tracks or floor markers.

## Key specifications

- **Payload:** up to 25 kg per pick.
- **Battery life:** 9 hours of continuous operation on a single charge.
- **Charging time:** 80 minutes to full from empty using the Atlas Dock.
- **Navigation:** LiDAR + camera fusion, no floor markers required.
- **Top speed:** 1.8 m/s when carrying a load, 2.5 m/s when empty.
- **Operating temperature:** 0°C to 40°C.

## Safety systems

The Atlas-7 stops within 30 cm when a person is detected in its path. It uses a
combination of LiDAR and an emergency bumper. The robot will not exceed 0.8 m/s
when a human is within two metres.

## Fleet management

A warehouse can run up to 50 Atlas-7 units under a single Fleet Controller. The
Fleet Controller assigns tasks, balances battery charging, and routes robots to
avoid congestion. Fleet software updates are delivered over the air and can be
scheduled outside operating hours.

## Warranty and support

The Atlas-7 ships with a two-year hardware warranty. Premium support customers
get a four-hour response time and on-site spare parts. Standard support response
time is one business day.
