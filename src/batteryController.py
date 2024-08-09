# -*- coding: utf-8 -*-

import sys
if sys.version_info[:2] == (3,10):
    import smbus2 as smbus
else:
    import smbus
import argparse
from config import log
import csv
import time
import json

DEBUG = False

BQ25887 = 0x6A

# Sensor limits
data_upper_limit = 100
data_lower_limit = 0

REG06_ADDRESS = 0x06

def delay_sec(count):
    while(count>1):
        count=count-1

def init(busNo):

    bus = smbus.SMBus(busNo)
    #disablecb(bus) 
    return bus

# Set the on and off states of the ADC
ADC_ON = 1
ADC_OFF = 0

def set_adc_state(bus, state):
    # Set the address of the ADC Control Register
    REG15_ADDRESS = 0x15
    # Set the bit position of the ADC_EN bit in REG15
    ADC_EN_BIT = 7
    # Read the current value of REG15
    reg15_value = bus.read_byte_data(BQ25887, REG15_ADDRESS)

    # Set the ADC_EN bit to the desired state
    if state == ADC_ON:
        reg15_value |= (1 << ADC_EN_BIT)
    elif state == ADC_OFF:
        reg15_value &= ~(1 << ADC_EN_BIT)
    # Write the new REG15 value to the BQ25887
    bus.write_byte_data(BQ25887, REG15_ADDRESS, reg15_value)
    # Wait for the new value to take effect
    delay_sec(0xFFFF)
    # Verify that the new REG15 value is written
    updated_reg15_value = bus.read_byte_data(BQ25887, REG15_ADDRESS)
    updated_adc_en = (updated_reg15_value >> ADC_EN_BIT) & 0x01
    # Print the new state of the ADC
    #!if DEBUG: print("ADC is now {}".format("enabled" if updated_adc_en else "disabled"))
    if DEBUG: log.info("ADC is now %s","enabled" if updated_adc_en else "disabled")
def set_max_cell_voltage(bus, voltage):
    REG00_ADDRESS = 0x00
    reg00_value = bus.read_byte_data(BQ25887, REG00_ADDRESS)
    
    voltage_step = (voltage - 3.40) * 1000 / 5  # Calculate the step value
    vcellreg = int(voltage_step) & 0xFF  # Convert the step value to an 8-bit integer
    
    new_reg00_value = (reg00_value & ~0xFF) | vcellreg  # Update the VCELLREG field
    bus.write_byte_data(BQ25887, REG00_ADDRESS, new_reg00_value)
    
    # Read back the register value and calculate the max cell voltage setting
    updated_reg00_value = bus.read_byte_data(BQ25887, REG00_ADDRESS)
    updated_vcellreg = updated_reg00_value & 0xFF
    updated_voltage = 3.40 + (updated_vcellreg * 5 / 1000)
    
    if DEBUG: print("Max cell voltage set to: {:.2f} V".format(updated_voltage))
    
def get_charging_status(bus):
    REG0B_ADDRESS = 0x0B
    reg0b_value = bus.read_byte_data(BQ25887, REG0B_ADDRESS)
    chrg_stat = reg0b_value & 0x07
    CHRG_STAT_DESCRIPTIONS = [
        "Not Charging",
        "Trickle Charge (VBAT < VBAT_SHORT)",
        "Pre-charge (VBAT_UVLO_RISING < VBAT < VBAT_LOWV)",
        "Fast-charge (CC mode)",
        "Taper Charge (CV mode)",
        "Top-off Timer Charging",
        "Charge Termination Done",
        "Reserved"
    ]

    if CHRG_STAT_DESCRIPTIONS[chrg_stat] == "Not Charging":
        return 0
    elif CHRG_STAT_DESCRIPTIONS[chrg_stat] == "Charge Termination Done":
        return 2
    elif CHRG_STAT_DESCRIPTIONS[chrg_stat] == "Reserved":
        return 3
    elif CHRG_STAT_DESCRIPTIONS[chrg_stat] == "Trickle Charge (VBAT < VBAT_SHORT)" or CHRG_STAT_DESCRIPTIONS[chrg_stat] == "Pre-charge (VBAT_UVLO_RISING < VBAT < VBAT_LOWV)" :
        return 4
    else:
        return 1

def get_power_status(bus):
    REG0C_ADDRESS = 0x0C  
    reg0c_value = bus.read_byte_data(BQ25887, REG0C_ADDRESS)

    pg_stat = (reg0c_value >> 7) & 0x01
    vbus_stat = (reg0c_value >> 4) & 0x07
    ico_stat = (reg0c_value >> 1) & 0x03

    vbus_stat_map = {
        0: "No Input",
        1: "USB Host SDP (PSEL High)",
        2: "USB CDP (1.5 A)",
        3: "Adapter (3.0 A, PSEL low)",
        4: "Charge Termination Done",
        5: "Unknown Adapter (500 mA)",
        6: "Reserved"
    }

    if vbus_stat_map[vbus_stat] == "No Input":
        return 0
    elif vbus_stat_map[vbus_stat] == "Charge Termination Done":
        return 2
    elif vbus_stat_map[vbus_stat] == "Reserved":
        return 3
    else:
        return 1

def read_vbat_voltage(bus):
    REG1D_ADDRESS = 0x1D
    REG1E_ADDRESS = 0x1E
    vbat_adc1_value = bus.read_byte_data(BQ25887, REG1D_ADDRESS)
    vbat_adc0_value = bus.read_byte_data(BQ25887, REG1E_ADDRESS)
    # Combine the two 8-bit register values into a 16-bit integer value
    vbat_adc_value = (vbat_adc1_value << 8) | vbat_adc0_value
    vbat_voltage = (vbat_adc_value) 

    return vbat_voltage

def toggle_en_chg(bus):
    REG06_ADDRESS = 0x06
    reg06_value = bus.read_byte_data(BQ25887, REG06_ADDRESS)
    en_chg = (reg06_value >> 3) & 0x01
    new_reg06_value = reg06_value ^ (1 << 3)  # toggle the EN_CHG bit
    bus.write_byte_data(BQ25887, REG06_ADDRESS, new_reg06_value)
    log.debug("EN_CHG register toggled from %s to %s.",en_chg, (new_reg06_value >> 3) & 0x01)

    # Set the EN_CHG bit back to 1
    new_reg06_value |= (1 << 3)
    bus.write_byte_data(BQ25887, REG06_ADDRESS, new_reg06_value)
    log.debug("EN_CHG register set back to 1.")

def get_vbus_ovp_stat(bus):
    REG11_ADDRESS = 0x11
    reg0e_value = bus.read_byte_data(BQ25887, REG11_ADDRESS)
    vbus_ovp_stat = (reg0e_value >> 7) & 0x01
    if vbus_ovp_stat:
        log.info("Device in over-voltage protection")
        return 3
    else:
        return 1  # Normal

def get_tshut_stat(bus):
    REG0E_ADDRESS = 0x0E
    reg0e_value = bus.read_byte_data(BQ25887, REG0E_ADDRESS)
    tshut_stat = (reg0e_value >> 6) & 0x01
    if tshut_stat:
        log.info("Device in thermal shutdown protection")
        return 3
    else:
        return 1  # Normal

def get_tmr_stat(bus):
    REG0E_ADDRESS = 0x0E
    reg0e_value = bus.read_byte_data(BQ25887, REG0E_ADDRESS)
    tmr_stat = (reg0e_value >> 4) & 0x01
    if tmr_stat:
        log.info("Charge safety timer expired")
        return 3
    else:
        return 1  # Normal


def readAll(bus):
#----------------------------read REG0B------------------------------
    bus = init(0)
    set_adc_state(bus, ADC_ON)
    REG0B_ADDRESS = 0x0B
    reg0b_value = bus.read_byte_data(BQ25887, REG0B_ADDRESS)

    iindpm_stat = (reg0b_value >> 6) & 0x01
    vindpm_stat = (reg0b_value >> 5) & 0x01
    treg_stat = (reg0b_value >> 4) & 0x01
    wd_stat = (reg0b_value >> 3) & 0x01
    chrg_stat = reg0b_value & 0x07

    CHRG_STAT_DESCRIPTIONS = [
        "Not Charging",
        "Trickle Charge (VBAT < VBAT_SHORT)",
        "Pre-charge (VBAT_UVLO_RISING < VBAT < VBAT_LOWV)",
        "Fast-charge (CC mode)",
        "Taper Charge (CV mode)",
        "Top-off Timer Charging",
        "Charge Termination Done",
        "Reserved"
    ]
    #print("REG0B value: 0x{:02X} ({})".format(reg0b_value, reg0b_value))
    #print("!!! IINDPM_STAT: {}".format("In IINDPM Regulation (ILIM pin or IINDPM register)" if iindpm_stat else "Normal"))
    #print("!!! VINDPM_STAT: {}".format("In VINDPM Regulation" if vindpm_stat else "Normal"))
    #print("!!! TREG_STAT: {}".format("In Thermal Regulation" if treg_stat else "Normal"))
    #print("!!! WD_STAT: {}".format("WD Timer expired" if wd_stat else "Normal"))
    print("!!! CHRG_STAT: {} ({})".format(chrg_stat, CHRG_STAT_DESCRIPTIONS[chrg_stat]))
    print("/////////////////////////////////////////////////")
#----------------------------read REG0C------------------------------
    REG0C_ADDRESS = 0x0C
    reg0c_data = bus.read_byte_data(BQ25887, REG0C_ADDRESS)

    # Read REG0C and print its value
    reg0c_value = reg0c_data
    
    print("REG0C value: 0x{:02X}".format(reg0c_value))
    pg_stat = (reg0c_value >> 7) & 0x01
    vbus_stat = (reg0c_value >> 4) & 0x07
    ico_stat = (reg0c_value >> 1) & 0x03
    
    vbus_stat_map = {
        0: "No Input",
        1: "USB Host SDP (PSEL High)",
        2: "USB CDP (1.5 A)",
        3: "Adapter (3.0 A, PSEL low)",
        4: "POORSRC detected 7 consecutive times",
        5: "Unknown Adapter (500 mA)",
        6: "Non-standard Adapter (1 A/2 A/2.1 A/2.4 A)"
    }
    ico_stat_map = {
        0: "ICO Disabled",
        1: "ICO Optimization is in progress",
        2: "Maximum input current detected",
        3: "Reserved"
    }
    print("!!! PG_STAT: {}".format("Power Good" if pg_stat else "Not Power Good"))
    print("!!! VBUS_STAT: {} ({})".format(vbus_stat_map[vbus_stat], vbus_stat))
    print("!!! ICO_STAT: {} ({})".format(ico_stat_map[ico_stat], ico_stat))
    #----------------------------read REG0E------------------------------
    REG0E_ADDRESS = 0x0E
    reg0e_data = bus.read_byte_data(BQ25887, REG0E_ADDRESS)
    reg0e_value = reg0e_data
   
    print("REG0E value: 0x{:02X} ({})".format(reg0e_value, reg0e_value))

    vbus_ovp_stat = (reg0e_value >> 7) & 0x01
    tshut_stat = (reg0e_value >> 6) & 0x01
    tmr_stat = (reg0e_value >> 4) & 0x01

    print("!!! VBUS_OVP_STAT: {}".format("Device in over-voltage protection" if vbus_ovp_stat else "Normal"))
    print("!!! TSHUT_STAT: {}".format("Device in thermal shutdown protection" if tshut_stat else "Normal"))
    print("!!! TMR_STAT: {}".format("Charge Safety timer expired" if tmr_stat else "Normal"))

    #----------------------------read REG0D------------------------------ 
    REG0D_ADDRESS = 0X0D
    reg0d_value = bus.read_byte_data(BQ25887, REG0D_ADDRESS)
    
    ts_stat = reg0d_value & 0x07
    ntc_status = {
        0b000: "Normal",
        0b010: "TS Warm",
        0b011: "TS Cool",
        0b101: "TS Cold",
        0b110: "TS Hot"
    }

    #print("! REG0D value: 0x{:02X} ({})".format(reg0d_value, reg0d_value))
    print("TS_STAT: {}".format(ntc_status.get(ts_stat, "Reserved")))

    #----------------------------read REG0F------------------------------ 
    
    REG0F_ADDRESS = 0x0F

    reg0f_value = bus.read_byte_data(BQ25887, REG0F_ADDRESS)

    iindpm_flag = (reg0f_value >> 6) & 0x01
    vindpm_flag = (reg0f_value >> 5) & 0x01
    treg_flag = (reg0f_value >> 4) & 0x01
    wd_flag = (reg0f_value >> 3) & 0x01
    chrg_flag = reg0f_value & 0x01

    print("REG0F value: 0x{:02X} ({})".format(reg0f_value, reg0f_value))
    #print("!!! IINDPM Regulation INT Flag: {}".format("IINDPM signal rising edge detected" if iindpm_flag else "Normal"))
    #print("!!! VINDPM Regulation INT Flag: {}".format("VINDPM signal rising edge detected" if vindpm_flag else "Normal"))
    print("!!! IC Temperature Regulation INT Flag: {}".format("TREG signal rising edge detected" if treg_flag else "Normal"))
    #print("!!! I2C Watchdog INT Flag: {}".format("WD_STAT signal rising edge detected" if wd_flag else "Normal"))
    print("!!! Charge Status INT Flag: {}".format("CHRG_STAT[2:0] bits changed (transition to any state)" if chrg_flag else "Normal"))    
 
    
    #----------------------------read REG01------------------------------       
    REG01_ADDRESS = 0x01

    # Read the current value of REG01
    reg01_value = bus.read_byte_data(BQ25887, REG01_ADDRESS)

    # Extract the current settings
    en_hiz = (reg01_value >> 7) & 0x01
    en_ilim = (reg01_value >> 6) & 0x01
    ichg = reg01_value & 0x3F

    # Print the current settings
    print("REG01 value: 0x{:02X} ({})".format(reg01_value, reg01_value))
    print("!!! EN_HIZ: {}".format("Enable" if en_hiz else "Disable"))
    print("!!! EN_ILIM: {}".format("Enable" if en_ilim else "Disable"))
    print("!!! ICHG: {} mA".format(50 * ichg))
       
    #----------------------------read REG02------------------------------
    REG02_ADDRESS = 0x02

    reg02_value = bus.read_byte_data(BQ25887, REG02_ADDRESS)

    en_vindpm_rst = (reg02_value >> 7) & 0x01
    en_bat_dischg = (reg02_value >> 6) & 0x01
    pfm_ooa_dis = (reg02_value >> 5) & 0x01
    vindpm = 3.9 + 0.1 * (reg02_value & 0x1F)

    print("REG02 value: 0x{:02X} ({})".format(reg02_value, reg02_value))
    #print("!!! EN_VINDPM_RST: {}".format("Enable VINDPM reset when adapter is plugged in (default)" if en_vindpm_rst else "Disable VINDPM reset when adapter is plugged in"))
    #print("!!! EN_BAT_DISCHG: {}".format("Enable BAT discharge load" if en_bat_dischg else "Disable load (Default)"))
    #print("!!! PFM_OOA_DIS: {}".format("Out-of-audio mode disabled while converter is in PFM" if pfm_ooa_dis else "Out-of-audio mode enabled while converter is in PFM (Default)"))
    #print("!!! VINDPM: {} V".format(vindpm))
    print("!!!/////////////////////////////////////////////////")

    #----------------------------read REG03------------------------------
    REG03_ADDRESS = 0x03
    reg03_data = bus.read_byte_data(BQ25887, REG03_ADDRESS)
    reg03_value = reg03_data
    print("REG03 value: 0x{:02X} ({})".format(reg03_value, reg03_value))

    force_ico = (reg03_value >> 7) & 0x01
    force_indet = (reg03_value >> 6) & 0x01
    en_ico = (reg03_value >> 5) & 0x01
    iindpm = reg03_value & 0x1F
    
    reg03_data = bus.read_byte_data(BQ25887, REG03_ADDRESS)
    reg03_value = reg03_data | 0b00100000
    bus.write_byte_data(BQ25887, REG03_ADDRESS, reg03_value)

    # Verify that EN_ICO bit is set to 1
    reg03_data = bus.read_byte_data(BQ25887, REG03_ADDRESS)
    en_ico = (reg03_data >> 5) & 0x01
    if en_ico:
        print("!ICO has been enabled")
    else:
        print("!Failed to enable ICO")

    print("!!! FORCE_ICO: {}".format("Force ICO start" if force_ico else "Do not force ICO (default)"))
    print("!!! FORCE_INDET: {}".format("Force PSEL detection" if force_indet else "Not in PSEL detection (default)"))
    print("!!! EN_ICO: {}".format("Enable ICO (default)" if en_ico else "Disable ICO"))

    input_current_limit = 500 + (iindpm * 100)
    if input_current_limit > 3300:
        input_current_limit = 3300
    print("!!! IINDPM: {} mA".format(input_current_limit))

#----------------------------read REG04------------------------------
    REG04_ADDRESS = 0x04
    reg04_value = bus.read_byte_data(BQ25887, REG04_ADDRESS)
    iprechg = ((reg04_value >> 4) & 0x0F) * 50  # Shift 4 bits to the right, mask with 0x0F, and multiply by 50 mA
    iterm = (reg04_value & 0x0F) * 50  # Mask with 0x0F and multiply by 50 mA

    print("REG04 value: 0x{:02X} ({})".format(reg04_value, reg04_value))
    print("!!! Precharge Current Limit: {} mA".format(iprechg))
    print("!!! Termination Current Limit: {} mA".format(iterm))
    print("/////////////////////////////////////////////////")

#----------------------------read REG05------------------------------------------------------------ 
    REG05_ADDRESS = 0x05

    # Read the current value of REG05
    reg05_value = bus.read_byte_data(BQ25887, REG05_ADDRESS)

    # Extract the current settings
    en_term = (reg05_value >> 7) & 0x01
    stat_dis = (reg05_value >> 6) & 0x01
    watchdog = (reg05_value >> 4) & 0x03
    en_timer = (reg05_value >> 3) & 0x01
    chg_timer = (reg05_value >> 1) & 0x03
    tmr2x_en = reg05_value & 0x01

    # Set the watchdog timer to 40 seconds
    reg05_value = (reg05_value & 0xCF) | (0b01 << 4)

    # Clear the TMR2X_EN bit (bit 0)
    reg05_value &= ~(1 << 0)

    # Write the new value to REG05
    bus.write_byte_data(BQ25887, REG05_ADDRESS, reg05_value)

    # Verify the new value
    reg05_value_new = bus.read_byte_data(BQ25887, REG05_ADDRESS)

    print("REG05 value (updated): 0x{:02X} ({})".format(reg05_value_new, reg05_value_new))
    #print("!!! Termination Control: {}".format("Enable" if en_term else "Disable"))
    print("!!! STAT Pin Disable: {}".format("Disable" if stat_dis else "Enable"))
    #print("!!! I2C Watchdog Timer Settings: {}".format({0: "Disable", 1: "40 s", 2: "80 s", 3: "160 s"}[watchdog]))
    #print("!!! Charging Safety Timer Enable: {}".format("Enable" if en_timer else "Disable"))
    #print("!!! Fast Charge Timer Setting: {}".format({0: "5 hrs", 1: "8 hrs", 2: "12 hrs", 3: "20 hrs"}[chg_timer]))
    #print("!!! Safety Timer during DPM or TREG: {}".format("Safety timer slowed by 2X" if tmr2x_en else "Safety timer always count normally"))    print("/////////////////////////////////////////////////")

    
 
#----------------------------read REG06------------------------------
    REG06_ADDRESS = 0x06
    
    reg06_value = bus.read_byte_data(BQ25887, REG06_ADDRESS)

    auto_indet_en = (reg06_value >> 6) & 0x01
    treg = (reg06_value >> 4) & 0x03
    en_chg = (reg06_value >> 3) & 0x01
    celllowv = (reg06_value >> 2) & 0x01
    vcell_rechg = reg06_value & 0x03

    treg_values = {0: "60°C", 1: "80°C", 2: "100°C", 3: "120°C"}
    vcell_rechg_values = {0: "50 mV", 1: "100 mV", 2: "150 mV", 3: "200 mV"}

    print("REG06 value: 0x{:02X} ({})".format(reg06_value, reg06_value))
    #print("!!! AUTO_INDET_EN: {}".format("Enable" if auto_indet_en else "Disable"))
    #print("!!! TREG: {}".format(treg_values[treg]))
    print("!!! EN_CHG: {}".format("Charge Enable" if en_chg else "Charge Disable"))
    #print("!!! CELLLOWV: {} V".format("3.0" if celllowv else "2.8"))
    #print("!!! VRECHG: {}".format(vcell_rechg_values[vcell_rechg]))
    print("!!! /////////////////////////////////////////////////") 
    
#----------------------------read REG10------------------------------
    
    REG10_ADDRESS = 0x10

    reg10_value = bus.read_byte_data(BQ25887, REG10_ADDRESS)

    pg_flag = (reg10_value >> 7) & 0x01
    vbus_flag = (reg10_value >> 4) & 0x01
    ts_flag = (reg10_value >> 2) & 0x01
    ico_flag = (reg10_value >> 1) & 0x01

    print("REG10 value: 0x{:02X} ({})".format(reg10_value, reg10_value))
    print("!!! PG_FLAG: {}".format("PG signal toggle detected" if pg_flag else "Normal"))
    #print("VBUS_FLAG: {}".format("VBUS_STAT[2:0] bits changed" if vbus_flag else "Normal"))
    #print("TS_FLAG: {}".format("TS_STAT[2:0] bits changed" if ts_flag else "Normal"))
    #print("ICO_FLAG: {}".format("ICO_STAT[1:0] changed" if ico_flag else "Normal"))
 
#----------------------------read REG11--------------------------------
    
    REG11_ADDRESS = 0x11

    reg11_value = bus.read_byte_data(BQ25887, REG11_ADDRESS)

    vb_oop_flag = (reg11_value >> 7) & 0x01
    tshut_flag = (reg11_value >> 6) & 0x01
    tmr_flag = (reg11_value >> 4) & 0x01

    print("REG11 value: 0x{:02X} ({})".format(reg11_value, reg11_value))
    print("!!! VBUS_OVP_FLAG: {}".format("Entered VBUS_OVP Fault" if vb_oop_flag else "Normal"))
    print("!!! TSHUT_FLAG: {}".format("Entered TSHUT Fault" if tshut_flag else "Normal"))
    print("!!! TMR_FLAG: {}".format("Charge Safety timer expired rising edge detected" if tmr_flag else "Normal"))
    print("/////////////////////////////////////////////////")  
#----------------------------read REG15--------------------------------
    
    REG15_ADDRESS = 0x15

    reg15_value = bus.read_byte_data(BQ25887, REG15_ADDRESS)

    adc_en = (reg15_value >> 7) & 0x01
    adc_rate = (reg15_value >> 6) & 0x01
    adc_sample = (reg15_value >> 4) & 0x03
    
    # Set bit 7 (ADC_EN) to 1 to enable the ADC
    new_reg15_value = reg15_value | (1 << 7)

    # Write the new REG15 value to the BQ25887
    bus.write_byte_data(BQ25887, REG15_ADDRESS, new_reg15_value)

    # Verify that the new REG15 value is written
    updated_reg15_value = bus.read_byte_data(BQ25887, REG15_ADDRESS)
    updated_adc_en = (updated_reg15_value >> 7) & 0x01  # Update the adc_en variable

    print("New REG15 value: 0x{:02X}".format(updated_reg15_value))
    print("!!! ADC_EN: {}".format("Enable ADC" if updated_adc_en else "Disable ADC"))

    print("!!! ADC_RATE: {}".format("One-shot conversion" if adc_rate else "Continuous conversion"))
    sys.stdout.write("!!! ADC_SAMPLE: ")
    #print("!!! ADC_SAMPLE: ", end="")

    if adc_sample == 0:
        print("15 bit effective resolution")
    elif adc_sample == 1:
        print("14 bit effective resolution")
    elif adc_sample == 2:
        print("13 bit effective resolution")
    elif adc_sample == 3:
        print("12 bit effective resolution")
    print("/////////////////////////////////////////////////")

#----------------------------read REG17&REG18&19&REG1A------------------------------
    REG17_ADDRESS = 0x17
    REG18_ADDRESS = 0x18
    REG19_ADDRESS = 0x19
    REG1A_ADDRESS = 0x1A

    # Read IBUS ADC values
    ibus_adc_high = bus.read_byte_data(BQ25887, REG17_ADDRESS)
    ibus_adc_low = bus.read_byte_data(BQ25887, REG18_ADDRESS)

    # Combine high and low byte values
    ibus_adc_value = (ibus_adc_high << 8) | ibus_adc_low

    # Read ICHG ADC values
    ichg_adc_high = bus.read_byte_data(BQ25887, REG19_ADDRESS)
    ichg_adc_low = bus.read_byte_data(BQ25887, REG1A_ADDRESS)

    # Combine high and low byte values
    ichg_adc_value = ((ichg_adc_high & 0x7F) << 8) | ichg_adc_low  # Mask high byte to remove the reserved bit

    print("IBUS_ADC: {} mA".format(ibus_adc_value))
    print("ICHG_ADC: {} mA".format(ichg_adc_value))
    
    print("!!! /////////////////////////////////////////////////")
 #----------------------------read REG1F&REG20------------------------------   
    REG1F_ADDRESS = 0x1F
    REG20_ADDRESS = 0x20

    # Read VCELLTOP ADC values
    vcelltop_adc_high = bus.read_byte_data(BQ25887, REG1F_ADDRESS)
    vcelltop_adc_low = bus.read_byte_data(BQ25887, REG20_ADDRESS)

    # Combine high and low byte values
    vcelltop_adc_value = (vcelltop_adc_high << 8) | vcelltop_adc_low

    def calculate_battery_percentage_from_voltage(voltage_V):
        min_voltage_V = 6000  # Minimum voltage of the two NR18650-35E batteries in series
        max_voltage_V = 8200  # Maximum voltage of the two NR18650-35E batteries in series

        # Calculate the percentage based on the given voltage
        battery_percentage = 100* ((voltage_V - min_voltage_V) / (max_voltage_V - min_voltage_V)) 
        
        return battery_percentage
        
    def read_battery_voltage_and_percentage():
        # Read VBAT_ADC values
        vbat_adc_high = bus.read_byte_data(BQ25887, 0x1D)
        vbat_adc_low = bus.read_byte_data(BQ25887, 0x1E)

        # Combine high and low byte values
        vbat_adc_value = (vbat_adc_high << 8) | vbat_adc_low

        # Convert ADC value to voltage
        voltage_V = vbat_adc_value 

        # Calculate battery percentage
        battery_percentage = calculate_battery_percentage_from_voltage(voltage_V)

        return voltage_V, battery_percentage

    # Read and print battery voltage and percentage
    battery_voltage, battery_percentage = read_battery_voltage_and_percentage()
    print("Battery Voltage: {:.2f} V".format(battery_voltage))
    print("Battery Percentage: {:.2f}%".format(battery_percentage))

    # Read VCELLTOP ADC values
    vcelltop_adc_high = bus.read_byte_data(BQ25887, REG1F_ADDRESS)
    vcelltop_adc_low = bus.read_byte_data(BQ25887, REG20_ADDRESS)

    # Combine high and low byte values
    vcelltop_adc_value = (vcelltop_adc_high << 8) | vcelltop_adc_low

    # Calculate voltage from VCELLTOP_ADC value
    vcelltop_voltage_V = vcelltop_adc_value * 0.001  # Convert ADC value to voltage

    print("!!! VCELLTOP_ADC: {} counts".format(vcelltop_adc_value))
    print("!!! VCELLTOP Voltage: {:.2f} V".format(vcelltop_voltage_V))
    

#----------------------------read REG28--------------------------------
    
    reg28_value = bus.read_byte_data(BQ25887, 0x28)
    print("REG28 value: 0x{:02X} ({})".format(reg28_value, reg28_value))

    # Decode the fields in register 0x28
    VDIFF_END_OFFSET = (reg28_value >> 5) & 0b111
    TCB_QUAL_INTERVAL = (reg28_value >> 4) & 0b1
    TCB_ACTIVE = (reg28_value >> 2) & 0b11
    TSETTLE = reg28_value & 0b11

    # Print a log description of the register values
    VDIFF_END_OFFSET_values = [30, 40, 50, 60, 70, 80, 90, 100]
    TCB_QUAL_INTERVAL_values = [2, 4]
    TCB_ACTIVE_values = [4, 32, 120, 240]
    TSETTLE_values = [10, 100, 1000, 2000]

    #print("!!! VDIFF_END_OFFSET: {} mV".format(VDIFF_END_OFFSET_values[VDIFF_END_OFFSET]))
    #print("!!! TCB_QUAL_INTERVAL: {} min".format(TCB_QUAL_INTERVAL_values[TCB_QUAL_INTERVAL]))
    #print("!!! TCB_ACTIVE: {} s".format(TCB_ACTIVE_values[TCB_ACTIVE]))
    #print("!!! TSETTLE: {} ms".format(TSETTLE_values[TSETTLE]))
#----------------------------read REG2A--------------------------------

    REG2A_ADDRESS = 0x2A

    reg2a_value = bus.read_byte_data(BQ25887, REG2A_ADDRESS)
    print("REG2A value: 0x{:02X} ({})".format(reg2a_value, reg2a_value))
    cb_chg_dis = (reg2a_value >> 7) & 0x01
    cb_auto_en = (reg2a_value >> 6) & 0x01
    cb_stat = (reg2a_value >> 5) & 0x01
    hs_cv_stat = (reg2a_value >> 4) & 0x01
    ls_cv_stat = (reg2a_value >> 3) & 0x01
    hs_ov_stat = (reg2a_value >> 2) & 0x01
    ls_ov_stat = (reg2a_value >> 1) & 0x01
    cb_oc_stat = reg2a_value & 0x01
    # Read the current value of REG2A
    reg2a_value = bus.read_byte_data(BQ25887, REG2A_ADDRESS)
    # Set the CB_AUTO_EN bit (bit 6) to enable cell balancing
    reg2a_value |= 1 << 6

    # Write the modified value back to REG2A
    bus.write_byte_data(BQ25887, REG2A_ADDRESS, reg2a_value)

    # Read the updated value of REG2A
    updated_reg2a_value = bus.read_byte_data(BQ25887, REG2A_ADDRESS)

    # Update the cb_auto_en variable based on the updated_reg2a_value
    updated_cb_auto_en = (updated_reg2a_value >> 6) & 0x01

    print("! Updated REG2A value: 0x{:02X} ({})".format(updated_reg2a_value, updated_reg2a_value))
    #print("!!! Updated CB_AUTO_EN: {}".format("Enable auto cell balancing (Default)" if updated_cb_auto_en else "Disable auto cell balancing"))

    #print("!!! CB_CHG_DIS: {}".format("Charge disabled during cell balancing cell voltage measurement (Default)" if cb_chg_dis else "Charge continuous during cell balancing cell voltage measurement"))
    #print("!!! CB_AUTO_EN: {}".format("Enable auto cell balancing (Default)" if cb_auto_en else "Disable auto cell balancing"))
    print("!!! CB_STAT: {}".format("Cell balance active mode" if cb_stat else "Cell balance not active or cell balance is exit"))
    #print("!!! HS_CV_STAT: {}".format("High side cell in CV mode" if hs_cv_stat else "High side cell not in CV mode"))
    #print("!!! LS_CV_STAT: {}".format("Low side cell in CV mode" if ls_cv_stat else "Low side cell not in CV mode"))
    #print("!!! HS_OV_STAT: {}".format("High side cell in over-voltage" if hs_ov_stat else "High side cell not in over-voltage"))
    #print("!!! LS_OV_STAT: {}".format("Low side cell in over-voltage" if ls_ov_stat else "Low side cell not in over-voltage"))
    print("!!! CB_OC_STAT: {}".format("Cell Balance Over-Current Protection active" if cb_oc_stat else "Cell Balance Over-Current Protection not active"))
    
    # charge_state = get_charging_status(bus)
    # print(charge_state)
    # log.info("Charge Status is: " + str(charge_state))
    
    bus.close()    
    # perV = 100*(VBATint-3500*2)/(4200*2-3500*2)
    # print(perV)    
def read(bus):  
    battery_status = -1 
    vovp_state = -1
    thermal_state = -1
    tmr_state = -1
    set_adc_state(bus, ADC_ON)
    delay_sec(0xFFFF)
    
    set_max_cell_voltage(bus, 4.15)
    
    vbat_voltage = read_vbat_voltage(bus)
    log.debug("VBAT voltage: %s",str(vbat_voltage))

    charge_state = get_charging_status(bus)
    power_state = get_power_status(bus)
    vovp_state = get_vbus_ovp_stat(bus)
    thermal_state = get_tshut_stat(bus)
    tmr_state = get_tmr_stat(bus)
    REG06_ADDRESS = 0x06
    reg06_value = bus.read_byte_data(BQ25887, REG06_ADDRESS)
    en_chg = (reg06_value >> 3) & 0x01
    
    log.debug("VBAT is: %s", str(vbat_voltage))
    
    min_voltage_V = 7500  # Minimum voltage of the two NR18650-35E batteries in series (to be discuss with Mustafa Güleryüz)
    max_voltage_V = 8000  # Maximum voltage of the two NR18650-35E batteries in series
    
    if vbat_voltage < max_voltage_V and  charge_state == 0:
        log.debug("Before Toggle Charge Status is: %s", str(charge_state))
        log.debug("Battery voltage is below threshold, toggling EN_CHG register...")
        toggle_en_chg(bus)
        delay_sec(0xFFFF)
        charge_state = get_charging_status(bus)
        log.debug("After Toggle Charge Status is: %s", str(charge_state))
    
    charge_state = get_charging_status(bus)  # get the updated charging status
    log.debug("Charge Status is: %s", str(charge_state))

    
    full_bat_percent = 100
    fault_code = -999
    perV = 100*(vbat_voltage - min_voltage_V) / (max_voltage_V - min_voltage_V)
    
    if (perV < data_lower_limit):
        perV = fault_code # no data
        
    elif data_upper_limit <= perV:
        perV = full_bat_percent
        

    log.debug("Battery Level: %s", str(perV))

    if (charge_state == 0 or power_state == 0) and (vovp_state != 3 and tmr_state != 3 and thermal_state != 3 ):
        log.debug("Charging status: 0 and Power status with no FAULT means not plugged ")
        battery_status = 0
        set_adc_state(bus, ADC_OFF) 
        bus.close()
        return perV, battery_status
    

    elif (charge_state == 1 or charge_state == 4) and power_state == 1:
        if (charge_state == 4) :
            log.debug("Charge Status is: %s", str(charge_state))
            log.debug("Power Status is: %s", str(power_state))  
            log.debug("Trickle or Pre-Charge mode")
            battery_status = 1 
            set_adc_state(bus, ADC_OFF) 
            bus.close()
            return 0, battery_status
        else:
            log.debug("Charge Status is: %s", str(charge_state))
            log.debug("Power Status is: %s", str(power_state))      
            log.debug("Fast or upper stage charging")
            battery_status = 1 
            set_adc_state(bus, ADC_OFF) 
            bus.close()
            return perV, battery_status
        
    elif (charge_state == 1 or charge_state == 2) or (power_state == 1 or power_state == 2):

        if perV >= full_bat_percent:
            log.debug("Charging status: %100 or more than capacity")
            battery_status = 1
            perV = full_bat_percent
            bus.close()
            return perV, battery_status
        else:
            battery_status = 1
            log.debug("Charging status: Not %100 almost capacity")
            bus.close()
            return perV, battery_status
        
    elif (charge_state == 3 or power_state == 3) and (vovp_state == 3 or tmr_state == 3 or thermal_state == 3 ):
        battery_status = 3
        log.debug("Charging status: 3 or Power status: 3 means --RESERVED-- ")
        bus.close()
        return fault_code, battery_status
    elif (charge_state == 0 and (power_state == 0 or power_state == 1)) and (vovp_state == 3 or tmr_state == 3 or thermal_state == 3):
        
        #log.info("Charge Status is: %s", str(charge_state))
        #log.info("Power Status is: %s", str(power_state))
        #log.info("Vovp Status is: %s", str(vovp_state))
        #log.info("TMR Status is: %s", str(tmr_state))
        #log.info("Thermal Status is: %s", str(thermal_state))
        battery_status = 3
        log.error("Charging status: --FAULT-- ")
        set_adc_state(bus, ADC_OFF) 
        bus.close()
        return fault_code, battery_status
    else:
        bus.close()
        return perV, battery_status

def ftc_mode(file):

    bus = init(0)
    data = read(bus)[0]
    print('''Data: %d ''' % data)

    output_json = {
        "serial_number": "null",
        "battery_level": str(data)
    }

    with open(file, 'w') as f:
        f.write(json.dumps(output_json))

    if (data <= data_upper_limit and data >= data_lower_limit):
        print("sensor value(s) are normal, OK")
        sys.exit(0)
    else:
        print("sensor value(s) are not within desired limits, FAIL")
        sys.exit(1)

def main():

    msg = "BQ25887 Power IC Python Module"
    help_msg = "RUN_MODE options: normal ftc, default:normal"
    help_msg_output_file = "OUTPUT_FILE: specify file path to write serial number and the other data, default: /tmp/battery_out"

    parser = argparse.ArgumentParser(description=msg)

    parser.add_argument("-r", "--run_mode", type=str, default="normal", required=False, help = help_msg)
    parser.add_argument("-o", "--output_file", type=str, default="/tmp/battery_out", required=False, help = help_msg_output_file)   

    args = parser.parse_args()

    if args.run_mode == "ftc":
        ftc_mode(args.output_file)

    bus = init(0)
    #disablecb(bus) 
    readAll(bus)
    read(bus)
    bus = init(0)
    perV, battery_status = read(bus)
    log.info("perV is: %s", str(perV))
    log.info("battery_status is: %s", str(battery_status))
    while True:
        perV, battery_status = read(bus)
        with open("/home/cairapp/battery_status.txt", "a") as file:
            file.write(str(battery_status) + ",")
            file.write(str(perV) + "\n")
        

    
    return perV, battery_status

if __name__ == '__main__':
    main() 