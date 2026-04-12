# central-load-plan

**Python 3**

`central-load-plan` watches a network location for files and generates configured output such as emails and other files.

This project was originally part of `lido-middleware` but was split off during upgrades to handle more "To:" addresses in emails, fixing issues where emails were failing to reach stations.


## LSYREPT

In production this program fetches crew members from the LSYREPT database. `flask lsyrept` includes commands to dump the necessary LSYREPT tables to CSV with a manifest json file that can be used to load this data into another database.
