# AdversarialMimicFuzzer
This is a tool to 'detonate' malware from afar in a separate system, testing something more dynamic than the static sandboxes currently
in use today.

Please sift through these sources before continuing

https://go.dev/doc/tutorial/fuzz
https://github.com/antonio-morales/fuzzing101
https://www.youtube.com/watch?v=5SORCfs-Mk0


Set Up Tool

Given the number of items that must be started to test the tool and to have it running, it oddly enough is easy to set up. As per my last tool, I have a requirements text file attached in the repository. Here are the following steps 

Pull down the repository 

Pip install –r requirements within the working directory 

Once these are installed, you could keep the WebServer.py and FuzzerCore.py files in a folder in a desired attacker VM (host) for testing, or you can keep it on the working directory; both methods of use work equally well. You may find it more practical to separate the files as described, as the tool is intended for fuzzing malware. If you do this, make sure to properly set up a virtual Python environment through the steps below: 

python3 -m venv venv && source venv/bin/activate pip  

install -r requirements.txt 

The agent.py file can be moved into the victim VM you want to test; this file does not require the dependencies listed in the requirements.txt file. You can then run this and the other files  

python3 (Agent.py/WebServer.py/FuzzerServer.py, etc,.) 

Keep in mind FuzzerServer is used as a command-line variant for the webtool and AdversaryFuzzer is used as an offline testing sandbox for the tool. The web server is hosted on your machine at http://127.0.0.1:5000/ . 

An example of its use, say if it against command-line tool, would be used like this 

./targetVulnerableApp --input <fuzzed_payload> 

Be sure to modify the result = subprocess.run array of strings in Agent.py to include the targeted app you want to fuzz! 
