# Northwind Robotics — Information Security Policy

## Scope

This policy applies to all employees, contractors, and the software running on
Atlas-7 robots and the Fleet Controller.

## Access control

Access to production systems follows least privilege. Every engineer authenticates
with single sign-on and a hardware security key; passwords alone are never
sufficient for production access. Access reviews are run quarterly, and access is
revoked within 24 hours of an employee leaving.

## Data classification

Data is classified as Public, Internal, Confidential, or Restricted. Customer
warehouse layouts and fleet telemetry are Confidential. Personal data of
employees is Restricted and may only be processed by the People team and
authorised systems.

## Robot and fleet security

Fleet software updates are signed and verified on the device before installation.
An Atlas-7 will refuse an update whose signature does not validate. Telemetry sent
from robots to the Fleet Controller is encrypted in transit using TLS 1.3.

## Incident response

Suspected security incidents must be reported to the Security team within one hour
of discovery. The Security team triages every report and leads containment.
Customers affected by a confirmed breach are notified within 72 hours, in line
with GDPR.

## Passwords and devices

Company laptops are encrypted at rest and locked after five minutes of inactivity.
Lost or stolen devices must be reported immediately so they can be remotely wiped.
