import keyboard
import time
from configUtils import setUpLogger 
log = setUpLogger()

class AuxController:
    def __init__(self, key=None):
        try:
            self.__key = key
            self.__value = 0
            #print("---- BEFORE PRESS ----") 
            keyboard.on_press_key(self.__key, self.__handle_press)
            #print("---- AFTER PRESS ----") 
            keyboard.on_release_key(self.__key, self.__handle_release)
            #print("---- AFTER RELEASE ----") 
        except:
            print("HATA")
        #log.info("Aux Init: Registration events for key %s is OK", self.__key)
        #print("Aux Init: Registration events for key ",self.__key," is OK")
    def __handle_press(self, event):
        self.__value = 0
        print("Key Pressed: ", self.__key)
        #log.info("Key Pressed: %s", self.__key)

    def __handle_release(self, event):
        self.__value = 1
        print("Key Released: ", self.__key)
        #log.info("Key Released: %s", self.__key)

    def value(self):
        return self.__value

# Example usage of AuxController
if __name__ == "__main__":
    

    try: 
        i = 0
        while i < 10000:
            aux_controller = AuxController('up')
            #print(aux_controller._AuxController__value)
            if aux_controller.value() == 1:
                print("Aux is pressed (value = 1)")
            else:
                print("Aux is not pressed (value = 0)")
            time.sleep(0.1)
            i += 1
    except KeyboardInterrupt:
        pass
