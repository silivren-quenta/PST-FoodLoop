from config import LOW_LEVEL, HIGH_LEVEL, TANK_CAPACITY

def get_pump_status(water_level):
    if water_level <= LOW_LEVEL:
        return "ON"
    elif water_level >= HIGH_LEVEL:
        return "OFF"
    return "ON"

def get_water_amount(water_level):
    return (water_level / 100) * TANK_CAPACITY