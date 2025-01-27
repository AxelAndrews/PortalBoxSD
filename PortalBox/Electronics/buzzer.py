import time
import machine
import logging

# Default values for buzzer frequency and duty cycle
defaultTone = 800.0
defaultDuty = 50.0
gpioBuzzerPin = 33  # The GPIO pin for buzzer

# Duration of each loop in milliseconds
loopMs = 100

# Frequencies of notes in the 4th octave
notes4thOctave = {
    "C":  261.63,
    "Db": 277.18,
    "D":  293.66,
    "Eb": 311.13,
    "E":  329.63,
    "F":  349.23,
    "Gb": 369.99,
    "G":  392,
    "Ab": 415.3,
    "A":  440,
    "Bb": 466.16,
    "B":  493.88
}

class Buzzer:
    """
    A simple class definition for the Buzzer that manages the sound effects like buzzing, beeping, and playing songs.
    """

    def __init__(self, buzzerPin=gpioBuzzerPin, pwmBuzzer=True):
        """
        Initialize the Buzzer object with a given pin and PWM control.
        """
        logging.info("Creating Buzzer Controller")
        self.buzzerPin = buzzerPin

        # If we don't have the hardware for PWM, don't set it up
        self.pwmBuzzer = pwmBuzzer
        self.buzzer = None
        if self.pwmBuzzer:
            # Use PWM if available, otherwise use regular GPIO output
            self.buzzer = machine.PWM(machine.Pin(self.buzzerPin), freq=defaultTone)
            self.buzzer.duty(int(defaultDuty * 1023 / 100))  # Set duty cycle (0-1023)
        else:
            self.buzzer = machine.Pin(self.buzzerPin, machine.Pin.OUT)

        # Whether it is currently playing a sound
        self.state = False

        # Flags for each state (singing, buzzing, beeping)
        self.isSinging = False
        self.songList = []

        self.isBuzzing = False
        self.buzzInfo = {
            "freq": -1,
            "numOfLoops": 0
        }

        self.isBeeping = False
        self.beepInfo = {
            "freq": -1,
            "durationMs": 0,
            "waitMs": 0,
            "effectTime": 0
        }

    def startBuzzer(self, freq=defaultTone, duty=defaultDuty):
        """
        Start the buzzer with a given frequency and duty cycle (PWM mode).
        """
        self.state = True
        if self.pwmBuzzer:
            self.buzzer.freq(freq)  # Set the frequency of the PWM
            self.buzzer.duty(int(duty * 1023 / 100))  # Set the duty cycle (0-1023)
        else:
            self.buzzer.value(1)  # Turn on the buzzer (no PWM)

    def stopBuzzer(self):
        """
        Stop the buzzer sound.
        """
        self.state = False
        if self.pwmBuzzer:
            self.buzzer.deinit()  # Disable PWM if used
        else:
            self.buzzer.value(0)  # Turn off the buzzer (no PWM)

    def createSongString(self, fileName, snLen=0.1, spacing=0.05):
        """
        Reads a song file and converts it into a list of notes with durations.
        """
        try:
            songFile = open(fileName, "r")
        except Exception as e:
            logging.error(f"Error opening file: {e}")
            return []

        freqList = []
        # Calculate the spacing between notes in terms of the number of loops
        loopSpacing = (spacing * 1000) // loopMs
        if loopSpacing < 1:
            loopSpacing = 1

        # Process each line/note in the song file
        for line in songFile:
            splitLine = line.split(",")
            noteOct = splitLine[0]

            # Split note and octave, handle flat notes (e.g., "Db")
            if noteOct[1] == "b":
                note = noteOct[0:2]
                octave = int(noteOct[2])
            else:
                note = noteOct[0]
                octave = int(noteOct[1])

            # Calculate the frequency based on the 4th octave reference
            freq = notes4thOctave[note] * (2 ** (octave - 4))

            # Calculate the length of the note in seconds
            length = float(splitLine[1]) * snLen

            # Calculate the number of loops for the note duration
            loopLength = (length * 1000) // loopMs
            if loopLength < 1:
                loopLength = 1

            # Add the note and its corresponding duration to the frequency list
            freqList.append([freq, loopLength])
            freqList.append([-1, loopSpacing])  # Add spacing after the note

        return freqList


def processCommand(command, buzzCon):
    """
    Process command strings to control the buzzer.
    """
    logging.debug("Buzzer Driver is processing a command")

    tokens = command.split()  # Split command into tokens
    params = [token for token in tokens[1:]]  # Get parameters

    if tokens[0] == "buzz":
        # Start buzzing with a given frequency for a specified duration
        if params[2] == "True":
            buzzCon.isSinging = False

        buzzCon.isBuzzing = True

        if params[3] == "True":
            buzzCon.isBeeping = False

        buzzCon.buzzInfo = {
            "freq": float(params[0]),
            "numOfLoops": (float(params[1]) * 1000) // loopMs  # Convert duration to loops
        }

    elif tokens[0] == "beep":
        # Start beeping with a given frequency and number of beeps
        buzzCon.isSinging = False
        buzzCon.isBuzzing = False
        buzzCon.isBeeping = True

        duration = float(params[1])
        beeps = int(params[2])

        # Calculate the duration of the wait between beeps
        waitMs = duration // (2 * beeps)
        waitMs = (waitMs + (loopMs // 2)) // loopMs * loopMs
        if waitMs < loopMs:
            waitMs = loopMs

        duration = waitMs * 2 * beeps  # Total duration of beeping

        buzzCon.beepInfo = {
            "freq": float(params[0]),
            "durationMs": duration,
            "waitMs": waitMs,
            "effectTime": 0
        }

    elif tokens[0] == "sing":
        # Start playing a song with a given file name and note length
        buzzCon.isSinging = True
        buzzCon.isBuzzing = False
        buzzCon.isBeeping = False
        buzzCon.songList = buzzCon.createSongString(params[0], float(params[1]), float(params[2]))

    elif tokens[0] == "stop":
        # Stop the current effect(s) (singing, buzzing, or beeping)
        if params[0] == "True":
            buzzCon.isSinging = False
        if params[1] == "True":
            buzzCon.isBuzzing = False
        if params[2] == "True":
            buzzCon.isBeeping = False

    else:
        logging.error(f"Unknown command: {tokens[0]}")
        return 1  # Error code if the command is not recognized

    return 0  # No error


def buzzerDriver(buzzerPin, pwmBuzzer):
    """
    Main loop of the buzzer driver, which checks for and handles different effects (singing, buzzing, beeping).
    """
    buzzCon = Buzzer(buzzerPin, pwmBuzzer)

    while True:
        if buzzCon.isSinging:
            # If the buzzer is playing a song, process the next note in the song
            if len(buzzCon.songList) > 0:
                freq, length = buzzCon.songList[0]

                # If the frequency is <= 0, stop the buzzer
                if freq <= 0 and buzzCon.state:
                    buzzCon.stopBuzzer()
                elif freq > 0 and not buzzCon.state:
                    buzzCon.startBuzzer(freq)  # Start the buzzer with the note's frequency

                # Decrease the length of the note and remove it if it's finished
                buzzCon.songList[0][1] -= 1
                if buzzCon.songList[0][1] <= 0:
                    buzzCon.songList.pop(0)

            else:
                buzzCon.stopBuzzer()  # Stop if the song is over
                buzzCon.isSinging = False

        if buzzCon.isBeeping:
            # If the buzzer is beeping, alternate between on and off based on the wait time
            if buzzCon.beepInfo["effectTime"] < buzzCon.beepInfo["durationMs"]:
                if (buzzCon.beepInfo["effectTime"] // buzzCon.beepInfo["waitMs"]) % 2 == 0:
                    buzzCon.startBuzzer(buzzCon.beepInfo["freq"])  # Start the buzzer
                else:
                    buzzCon.stopBuzzer()  # Stop the buzzer

                # Increase the effect time to keep track of the beep duration
                buzzCon.beepInfo["effectTime"] += loopMs
            else:
                buzzCon.stopBuzzer()  # Stop after the duration is complete
                buzzCon.isBeeping = False

        if buzzCon.isBuzzing:
            # If the buzzer is buzzing, continue buzzing for the specified number of loops
            if buzzCon.buzzInfo["numOfLoops"] > 0:
                if not buzzCon.state:
                    buzzCon.startBuzzer(buzzCon.buzzInfo["freq"])  # Start the buzzer
                buzzCon.buzzInfo["numOfLoops"] -= 1  # Decrease the loop count
            else:
                buzzCon.stopBuzzer()  # Stop after all loops are done
                buzzCon.isBuzzing = False

        # If no effect is active, ensure the buzzer is off
        if not (buzzCon.isBuzzing or buzzCon.isBeeping or buzzCon.isSinging):
            buzzCon.stopBuzzer()

        time.sleep(loopMs / 1000)  # Delay to maintain the loop's timing

# Running the buzzer driver in the main loop
buzzerDriver(gpioBuzzerPin, pwmBuzzer=True)
