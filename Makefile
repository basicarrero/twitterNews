install:
		sudo apt-get install python-pip python-twill python-imaging-tk python-beautifulsoup python-tweepy
		sudo pip install spade

run:
		configure.py 127.0.0.1
		x-terminal-emulator -e runspade.py
		sleep 1
		python MyAgent.py

cleanconf:
		rm *.xml

clean:
		rm *.xml
		rm dataObject
