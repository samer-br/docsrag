# New Engineer Onboarding Guide

## Your first week

Welcome to Northwind Robotics! In your first week you will get your hardware
security key, set up single sign-on, and be added to your team. Your home-office
budget of 8,000 SEK is available from day one — order through the Equipment portal.

## Development environment

All services run locally with Docker. Clone the `fleet-controller` repository and
run `docker compose up` to start the simulator, which lets you test robot
behaviour without physical hardware. The simulator can model a fleet of up to 50
virtual Atlas-7 units.

## Deploying changes

Changes reach production through a pull request, a green CI run, and one approval
from a code owner. Production deploys happen behind a feature flag; nothing ships
to live robots without a signed build, in line with the security policy.

## Who to ask

- **Fleet routing and navigation:** the Autonomy team.
- **Battery and charging behaviour:** the Hardware team.
- **Anything about access, keys, or incidents:** the Security team.
- **Vacation, expenses, remote work:** the People team or the Employee Handbook.

## On-call

Engineers join the on-call rotation after three months. On-call covers the Fleet
Controller and the update pipeline. The on-call engineer acknowledges alerts
within 15 minutes and has a runbook for the most common fleet incidents.
