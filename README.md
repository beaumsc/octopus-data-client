# API

[API details](https://developer.octopus.energy/docs/api/)

API Datetimes in query string are ISO8601 zulu format. Data fetched is localtime with offset.
Database datetimes are stored as strings and are naive (no UTC offset) owing to limitation of SQLite.
