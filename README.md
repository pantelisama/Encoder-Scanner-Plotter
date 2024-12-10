Serial interface connects to a serial terminal
Sends specific commands into the terminal
Scraps pan,tilt,height raw encoder data 
Creates timestamp
Prints timestamp,pan,tilt,height
Plots all 3 axis

TCP interface connects to a TCP Client 
Sends specific commands to the server
Scraps pan,tilt,height interpolated data
Creates timestamp
Prints timestamp,pan,tilt,height
Plots all 3 axis


These tools have been created for testing the reliability of the 3 encoder signals. Observation of noises and drifting of encoder counts.
The option to log and export data gives us a great way to compare different firmware versions of the Multiaxis processor. The 
processor which is reponsible for reading and interpolating the encoder counts of the robot.
