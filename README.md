# homed

- Install `pipenv`
- Install dependencies with `pipenv install`
- Install Adafruit Python library : 
  - `cd ..`
  - `git clone https://github.com/adafruit/Adafruit_Python_DHT.git`
  - `cd homed`
  - `pipenv shell`
  - `cd ../Adafruit_Python_DHT`
  - `python setup.py install`
- Link pigpiod service with `sudo ln -s /etc/systemd/system/pigpiod.service ./pigpiod.service`
- Link service with `sudo ln -s /etc/systemd/system/homed.service ./homed.service`
 
Now that all is ready, setup .env file with openweathermap API key (see template).
