# Electricity Use and Export Data Collector and Analyser

Collects electricity usage and exports from Octopus API. Analysis of data to validate or aid the selection of the best tariff available.

## References
[Octopus API details](https://developer.octopus.energy/docs/api/)

## Date time handling

### Octopus API
The API is a mix of localtime and UTC depending on context.

* Remote data collection tends to end on midnight UTC of the previous day.
* Query string is expected to be UTC timezone and ISO8601 Z suffix format.
* Period start and end times of data records received is localtime with offset.

### Considerations
* Much of the processing needed is to be accounted per day.
* Tariff time slots are based on local time. Fair to assume never nearby midnight.
* Octopus billing is based on local time
* If basing on whole day localtime usage there would be an extra day latency when DST applies
* Calculation based on available UTC day cut-offs would suffice
* It is generally good practice to work in UTC and convert to localtime on human interfaces

### Handling within this code
The ORM is configured to convert from and to local time zone on the interface to the database. Thus, the majority of this code is working in localtime.
