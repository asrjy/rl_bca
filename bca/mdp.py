from emspy import utils, MdpManager


# -- All encoding/normalization functions below. MUST TAKE value of element as first argument --

def encode_none(value):
    """Pass value to encoded value, no encoding."""
    return value


def normalize_min_max_strict(value, min: float, max: float):
    lower = -1
    upper = 1
    if max < value < min:
        raise ValueError(f'Value {value} is great than {max} OR less than {min}. Use saturated version.')
    else:
        return ((value - min) / (max - min))*(upper - lower) + lower


def normalize_min_max_saturate(value: float, min: float, max: float):
    lower = -1
    upper = 1
    if value > max:
        return upper
    elif value < min:
        return lower
    else:
        return ((value - min) / (max - min))*(upper - lower) + lower


def digitize_bool(value: bool):
    return float(value)


# ENCODING PARAMS
# indoor temp bounds, IDD - C, -70-70
indoor_temp_max = 30
indoor_temp_min = 15
# electricity
# PV_gen_max =


# STATE SPACE (& Auxiliary Simulation Data)
zn0 = 'Core_ZN ZN'
zn1 = 'Perimeter_ZN_1 ZN'
zn2 = 'Perimeter_ZN_2 ZN'
zn3 = 'Perimeter_ZN_3 ZN'
zn4 = 'Perimeter_ZN_4 ZN'

# --- create EMS Table of Contents (TC) for sensors/actuators ---
# int_vars_tc = {"attr_handle_name": "variable_type", "variable_key"],...}
# vars_tc = {"attr_handle_name": ["variable_type", "variable_key"],...}
# meters_tc = {"attr_handle_name": "meter_name",...}
# actuators_tc = {"attr_handle_name": ["component_type", "control_type", "actuator_key"],...}
# weather_tc = {"attr_name": "weather_metric",...}

# RULES:
# - any EMS var must contain at least handle information.
# - encoding functions are optional, as are their args
# - encoding functions must take in that EMS "value" as first argument, but not excluded in args below, its implied.
# - IF encoding function requires args that are not static numbers and need to be computed at runtime manually, input
#   "None" for this arg, this will return a "None" encoding, notifying encoding must still be done

year = '2019'

tc_intvars = {}

tc_vars = {
    # Building
    'hvac_operation_sched': [('Schedule Value', 'OfficeSmall HVACOperationSchd')],  # is building 'open'/'close'?
    # 'hvac_operation_sched': [('Schedule Value', 'CJE Always ON HVACOperationSchd')],  # is building 'open'/'close'?
    # 'PV_generation': [('Generator Produced DC Electricity Energy', 'Generator Photovoltaic 1')],  # [J] HVAC, Sum
    # Schedule Files
    # $rtp
    'rtp': [('Schedule Value', f'ERCOT RTM {year}'), normalize_min_max_saturate, 0, 500],
    'dap0': [('Schedule Value', f'ERCOT DAM 12-Hr Forecast {year} - 0hr Ahead'), normalize_min_max_saturate, 0, 1000],
    'dap1': [('Schedule Value', f'ERCOT DAM 12-Hr Forecast {year} - 1hr Ahead'), normalize_min_max_saturate, 0, 1000],
    'dap2': [('Schedule Value', f'ERCOT DAM 12-Hr Forecast {year} - 2hr Ahead'), normalize_min_max_saturate, 0, 1000],
    'dap3': [('Schedule Value', f'ERCOT DAM 12-Hr Forecast {year} - 3hr Ahead'), normalize_min_max_saturate, 0, 1000],
    'dap4': [('Schedule Value', f'ERCOT DAM 12-Hr Forecast {year} - 4hr Ahead'), normalize_min_max_saturate, 0, 1000],
    'dap5': [('Schedule Value', f'ERCOT DAM 12-Hr Forecast {year} - 5hr Ahead'), normalize_min_max_saturate, 0, 1000],
    'dap6': [('Schedule Value', f'ERCOT DAM 12-Hr Forecast {year} - 6hr Ahead'), normalize_min_max_saturate, 0, 1000],
    # fuel mix
    'wind_gen': [('Schedule Value', f'ERCOT FMIX {year} - Wind'), normalize_min_max_saturate, 0, 3700],
    'solar_gen': [('Schedule Value', f'ERCOT FMIX {year} - Solar'), normalize_min_max_saturate, 0, 300],
    'total_gen': [('Schedule Value', f'ERCOT FMIX {year} - Total'), normalize_min_max_saturate, 0, 14000],
    # -- Zone 0 --
    'zn0_temp': [('Zone Air Temperature', zn0), normalize_min_max_saturate, indoor_temp_min, indoor_temp_max],
    # 'zn0_RH': [('Zone Air Relative Humidity', zn0), normalize_high_low_saturate, utils.f_to_c(0), utils.f_to_c(100)],
    'zn0_cooling_sp_var': [('Zone Thermostat Cooling Setpoint Temperature', zn0), normalize_min_max_saturate, indoor_temp_min, indoor_temp_max],
    # 'zn0_heating_sp_var': [('Zone Thermostat Heating Setpoint Temperature', zn0)],
    # 'zn0_fan_electricity': [('Fan Electricity Energy', zn0)],
    # -- Zone 1 --
    'zn1_temp': [('Zone Air Temperature', zn1), normalize_min_max_saturate, indoor_temp_min, indoor_temp_max],
    # 'zn1_RH': [('Zone Air Relative Humidity', zn1), normalize_high_low_saturate, utils.f_to_c(0), utils.f_to_c(100)],
    'zn1_cooling_sp_var': [('Zone Thermostat Cooling Setpoint Temperature', zn1), normalize_min_max_saturate, indoor_temp_min, indoor_temp_max],
    # 'zn1_heating_sp_var': [('Zone Thermostat Heating Setpoint Temperature', zn1)],
    # 'zn1_fan_electricity': [('Fan Electricity Energy', zn1)],
    # -- Zone 2 --
    'zn2_temp': [('Zone Air Temperature', zn2), normalize_min_max_saturate, indoor_temp_min, indoor_temp_max],
    # 'zn2_RH': [('Zone Air Relative Humidity', zn2), normalize_high_low_saturate, utils.f_to_c(0), utils.f_to_c(100)],
    'zn2_cooling_sp_var': [('Zone Thermostat Cooling Setpoint Temperature', zn2), normalize_min_max_saturate, indoor_temp_min, indoor_temp_max],
    # 'zn2_heating_sp_var': [('Zone Thermostat Heating Setpoint Temperature', zn2)],
    # 'zn2_fan_electricity': [('Fan Electricity Energy', zn2)],
    # -- Zone 3 --
    'zn3_temp': [('Zone Air Temperature', zn3), normalize_min_max_saturate, indoor_temp_min, indoor_temp_max],
    # 'zn3_RH': [('Zone Air Relative Humidity', zn3), normalize_high_low_saturate, utils.f_to_c(0), utils.f_to_c(100)],
    'zn3_cooling_sp_var': [('Zone Thermostat Cooling Setpoint Temperature', zn3), normalize_min_max_saturate, indoor_temp_min, indoor_temp_max],
    # 'zn3_heating_sp_var': [('Zone Thermostat Heating Setpoint Temperature', zn3)],
    # 'zn3_fan_electricity': [('Fan Electricity Energy', zn3)],
    # -- Zone 4 --
    # 'zn4_temp': [('Zone Air Temperature', zn4), normalize_min_max_saturate, indoor_temp_min, indoor_temp_max],
    # 'zn4_RH': [('Zone Air Relative Humidity', zn4), normalize_high_low_saturate, utils.f_to_c(0), utils.f_to_c(100)],
    # 'zn4_cooling_sp_var': [('Zone Thermostat Cooling Setpoint Temperature', zn4), normalize_min_max_saturate, indoor_temp_min, indoor_temp_max],
    # 'zn4_heating_sp_var': [('Zone Thermostat Heating Setpoint Temperature', zn4)],
    # 'zn4_fan_electricity': ['Fan Electricity Energy', zn4],
}

tc_meters = {
    # Building-wide
    # 'electricity_facility': ['Electricity:Facility'],
    'electricity_HVAC': ['Electricity:HVAC', normalize_min_max_saturate, 0, 690000],
    # 'electricity_heating': ['Heating:Electricity'],
    # 'electricity_cooling': ['Cooling:Electricity'],
    # 'gas_heating': ['NaturalGas:HVAC'],
    # Solar (custom)
    # 'PV_generation_meter': ['Solar Generation'],
    # -- Zn0 (custom meters) --
    'zn0_heating_electricity': ['Zn0 HVAC Heating Electricity', normalize_min_max_saturate, 0, 141000],
    # 'zn0_heating_gas': ['Zn0 HVAC Heating Natural Gas'],
    'zn0_cooling_electricity': ['Zn0 HVAC Cooling Electricity', normalize_min_max_saturate, 0, 142000],
    'zn0_fan_electricity': ['Zn0 HVAC Fan Electricity', normalize_min_max_saturate, 0, 22000],
    # -- Zn1 (custom meters) --
    'zn1_heating_electricity': ['Zn1 HVAC Heating Electricity', normalize_min_max_saturate, 0, 182000],
    # 'zn1_heating_gas': ['Zn1 HVAC Heating Natural Gas'],
    'zn1_cooling_electricity': ['Zn1 HVAC Cooling Electricity', normalize_min_max_saturate, 0, 154000],
    'zn1_fan_electricity': ['Zn1 HVAC Fan Electricity', normalize_min_max_saturate, 0, 24000],
    # -- Zn2 (custom meters) --
    'zn2_heating_electricity': ['Zn2 HVAC Heating Electricity', normalize_min_max_saturate, 0, 146000],
    # 'zn2_heating_gas': ['Zn2 HVAC Heating Natural Gas'],
    'zn2_cooling_electricity': ['Zn2 HVAC Cooling Electricity', normalize_min_max_saturate, 0, 111000],
    'zn2_fan_electricity': ['Zn2 HVAC Fan Electricity', normalize_min_max_saturate, 0, 18000],
    # -- Zn3 (custom meters) --
    'zn3_heating_electricity': ['Zn3 HVAC Heating Electricity', normalize_min_max_saturate, 0, 169000],
    # 'zn3_heating_gas': ['Zn3 HVAC Heating Natural Gas'],
    'zn3_cooling_electricity': ['Zn3 HVAC Cooling Electricity', normalize_min_max_saturate, 0, 139000],
    'zn3_fan_electricity': ['Zn3 HVAC Fan Electricity', normalize_min_max_saturate, 0, 21000],
    # -- Zn4 (custom meters) --
    # 'zn4_heating_electricity': ['Zn4 HVAC Heating Electricity', normalize_min_max_saturate, 0, 162000],  # TODO update
    # 'zn4_heating_gas': ['Zn4 HVAC Heating Natural Gas'],
    # 'zn4_cooling_electricity': ['Zn4 HVAC Cooling Electricity', normalize_min_max_saturate, 0, 135000],  # TODO update
    # 'zn4_fan_electricity': ['Zn4 HVAC Fan Electricity', normalize_min_max_saturate, 0, 22000]  # TODO update

}

tc_weather = {  # used for current and forecasted weather
    'oa_rh': ['outdoor_relative_humidity', normalize_min_max_saturate, 0, 100],  # IDD - %RH, 0-110
    'oa_db': ['outdoor_dry_bulb', normalize_min_max_saturate, utils.f_to_c(20), utils.f_to_c(100)],  # IDD - C, -70-70
    'oa_pa': ['outdoor_barometric_pressure', normalize_min_max_saturate, 90000, 120000],  # IDD - Pa, 31000-120000
    'sun_up': ['sun_is_up', digitize_bool],  # T/F
    'rain': ['is_raining', digitize_bool],  # T/F
    # 'snow': ['is_snowing', digitize_bool],  # T/F
    'wind_dir': ['wind_direction', normalize_min_max_strict, 0, 360],  # IDD - deg, 0-360
    'wind_speed': ['wind_speed', normalize_min_max_strict, 0, 400]  # IDD - m/s, 0-40
}

# ACTION SPACE (& Auxiliary Control)
tc_actuators = {
    # -- CONTROL --
    # HVAC Control Setpoints
    'zn0_cooling_sp': [('Zone Temperature Control', 'Cooling Setpoint', zn0)],
    'zn0_heating_sp': [('Zone Temperature Control', 'Heating Setpoint', zn0)],
    'zn1_cooling_sp': [('Zone Temperature Control', 'Cooling Setpoint', zn1)],
    'zn1_heating_sp': [('Zone Temperature Control', 'Heating Setpoint', zn1)],
    'zn2_cooling_sp': [('Zone Temperature Control', 'Cooling Setpoint', zn2)],
    'zn2_heating_sp': [('Zone Temperature Control', 'Heating Setpoint', zn2)],
    'zn3_cooling_sp': [('Zone Temperature Control', 'Cooling Setpoint', zn3)],
    'zn3_heating_sp': [('Zone Temperature Control', 'Heating Setpoint', zn3)],
    'zn4_cooling_sp': [('Zone Temperature Control', 'Cooling Setpoint', zn4)],
    'zn4_heating_sp': [('Zone Temperature Control', 'Heating Setpoint', zn4)],
}


if __name__ == "__main__":
    mdp_instance = MdpManager.generate_mdp_from_tc(tc_intvars, tc_vars, tc_meters, tc_weather, tc_actuators)
