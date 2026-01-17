# RDZ-MQTT-server
This is MQTT (with mosquitto) server for handle radiosonde data received from RDZ_TTGO via MQTT (JSON). Tested only with Windows 7 64bit, but with minor changes work too with Linux. 

Version 2 (17.01.2026)
A button has been added to the main form to display the map. When the button is clicked, the default web browser opens and shows a Leaflet map with markers of the received sondes from the database. The sondes are displayed in different colors: green for those within the last 2 hours and ascending, red for those within the last 2 hours and descending, yellow for those older than 2 hours and ascending, and purple for those older than 2 hours and descending. Two checkboxes have also been added: one to filter sondes to only those within the last 24 hours, and another for automatic tracking of the sonde that is currently in flight.

