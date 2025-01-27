This directory will become a Docker container for our project.

3/4 containers:

- Firmware: uses the Espressif IoT Development Framework Image. This will have tools that can be used for flashing/debugging the ESP.
- - - To develop firmware, make changes in the box_firmware directory. Then flash with the tools after running the containter.
   
- Database: for initial development, the database will be created from the schema and stored in the Docker image itself in a volume.
- - - We can change these endpoints later on for actual development/deployment.
   
- Portal: uses Apache/NGINX (unsure) and PHP+SOMETHING (unsure) to run the web app and websocket. We probably want to start with local hosting here.
- - - Starting on a common localhost port, then we will connect the actual endpoints once ready.
    - This section might actually be two separate containers, I'm a little unsure here.
