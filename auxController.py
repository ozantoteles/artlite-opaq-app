import keyboard
import time
from configUtils import setUpLogger 
log = setUpLogger()

class AuxController:
    def __init__(self, key=None):
        
        self.__key = key
        self.__value = 0
        keyboard.on_press_key(self.__key, self.__handle_press)
        keyboard.on_release_key(self.__key, self.__handle_release)
        log.info("Aux Init: Registration events for key %s is OK", self.__key)

    def __handle_press(self, event):
        self.__value = 1
        log.info("Key Pressed: %s", self.__key)

    def __handle_release(self, event):
        self.__value = 0
        log.info("Key Released: %s", self.__key)

    def value(self):
        return self.__value

# Example usage of AuxController
if __name__ == "__main__":
    aux_controller = AuxController('up')

    try:
        while True:
            if aux_controller.value() == 1:
                print("Aux is pressed (value = 1)")
            else:
                print("Aux is not pressed (value = 0)")
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
