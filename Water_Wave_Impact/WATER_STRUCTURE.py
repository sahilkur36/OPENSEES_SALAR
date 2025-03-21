###########################################################################################################
#                                                 IN THE NAME OF ALLAH                                    #
#            DYNAMIC RESPONSE ANALYSIS OF A SINGLE-DEGREE-OF-FREEDOM (SDOF) SYSTEM SUBJECTED              #
#                                   TO WATER IMPACT LOADING USING OPENSEES                                #
#---------------------------------------------------------------------------------------------------------# 
#                                   THIS PROGRAM IS WRITTEN BY SALAR DELAVAR GHASHGHAEI                   #
#                                          EMAIL: SALAR.D.GHASHGHAEI@GMAIL.COM                            #
###########################################################################################################
#
# Target:  
# This code models and analyzes the dynamic response of an SDOF structural system under time-varying water impact pressure.
# The objectives include:  
#
# 1. Water Impact Pressure Time Series Generation:  
#    - Implements a flexible waveform generator for water pressure loading, supporting sine, cosine, combined sine+cosine, triangle, and square waveforms.  
#    - Visualizes the generated water impact pressure time series.
#
# 2. Structural Model Development:  
#    - Constructs an SDOF system in OpenSeesPy with specified stiffness (`k`), mass (`m`), and damping ratio.  
#    - Applies the water pressure as a dynamic load to the system.  
#
# 3. Dynamic Analysis:  
#    - Conducts transient analysis using the Newmark integration method.  
#    - Monitors key responses, including displacement, velocity, acceleration, and base reaction forces over time.  
#
# 4. Visualization:  
#    - Provides time-history plots for displacement, velocity, acceleration, and base reaction forces to understand the structural response to water impact loading.
#
# This simulation aids engineers and researchers in evaluating the structural resilience of systems subjected to varying water impact pressures,
# applicable in contexts such as wave impact, fluid-structure interactions, and coastal engineering scenarios.
import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt

# Define structure parameters
k = 1.0e6  # Stiffness of the structure (N/m)
m = 1000.0  # Mass of the structure (kg)
damping_ratio = 0.05  # Damping ratio

# Define water impact pressure parameters
impact_duration = 2.0  # Total duration of water impact (s)
duration = 10.0  # Total simulation duration (s)
dt = 0.01  # Time step (s)
"""
def water_impact_time_series(impact_duration, dt):
    time = np.arange(0, impact_duration, dt)
    pressure = np.sin(2 * np.pi * time / impact_duration) * 1e4  # Example sinusoidal impact
    return time, pressure
"""    

def water_impact_time_series(impact_duration, dt, wave_type='sin+cos', frequency_factor=1.0, amplitude=1e4):
    """
    Generate a time series of water impact pressure over time.
    
    Parameters:
    - impact_duration: Duration of the impact event (seconds).
    - dt: Time step for the time series (seconds).
    - wave_type: Type of waveform ('sine', 'triangle', 'square'). Default is 'sine'.
    - frequency_factor: Factor to modify the frequency of the waveform. Default is 1.0.
    - amplitude: Amplitude of the waveform. Default is 1e4.
    
    Returns:
    - time: Array of time values.
    - pressure: Array of pressure values based on the chosen waveform.
    """
    time = np.arange(0, impact_duration, dt)
    frequency = frequency_factor / impact_duration  # Adjust frequency based on the impact duration

    if wave_type == 'sine':
        pressure = np.sin(2 * np.pi * frequency * time) * amplitude
    elif wave_type == 'cos':
        pressure = np.cos(2 * np.pi * frequency * time) * amplitude 
    elif wave_type == 'sin+cos':
        pressure = (np.sin(5 * np.pi * frequency * time) + np.cos(2 * np.pi * frequency * time)) * amplitude            
    elif wave_type == 'triangle':
        pressure = 2 * amplitude * np.abs(2 * (time * frequency % 1) - 1) - amplitude
    elif wave_type == 'square':
        pressure = amplitude * np.sign(np.sin(2 * np.pi * frequency * time))
    else:
        raise ValueError("Unsupported wave type. Choose from 'sine', 'triangle', or 'square'.")
    
    return time, pressure
    



# Generate water impact pressure time series
time_series, water_pressure = water_impact_time_series(impact_duration, dt)

def plot_water_impact_time_series(time, pressure):
    # Plot the pressure time history
    plt.figure(figsize=(10, 6))
    plt.plot(time, pressure, label='Water Wave Pressure', color='blue')
    plt.xlabel('Time (s)')
    plt.ylabel('Pressure Force (N)')
    plt.title('Water Wave Pressure Loading')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

# Plot the Water loading
plot_water_impact_time_series(time_series, water_pressure)

# Initialize OpenSees model
ops.wipe()
ops.model('basic', '-ndm', 1, '-ndf', 1)

# Define nodes
ops.node(1, 0.0)  # Fixed base
ops.node(2, 0.0)  # Mass node

# Define boundary conditions
ops.fix(1, 1)

# Define mass
ops.mass(2, m)

# Natural frequency (rad/s)
wn = (k / m) ** 0.5
# Damping coefficient (Ns/m)
CS = 2 * wn * m * damping_ratio

# Define material properties
ops.uniaxialMaterial('Elastic', 1, k)
# Define materials for structure damper
ops.uniaxialMaterial('Elastic', 2, 0.0, CS)

# Define element
#ops.element('Truss', 1, 1, 2, 1.0, 1)
ops.element('zeroLength', 1, 1, 2, '-mat', 1, 2, '-dir', 1, 1) # DOF[1] LATERAL SPRING 

# Apply time-dependent water impact loading
time_series_tag = 1
pattern_tag = 1
ops.timeSeries('Path', time_series_tag, '-dt', dt, '-values', *water_pressure)
ops.pattern('Plain', pattern_tag, time_series_tag)
ops.load(2, 1.0)  # Load applied to the mass node

# Set analysis parameters
ops.constraints('Plain')
ops.numberer('Plain')
ops.system('BandGeneral')
ops.test('NormDispIncr', 1.0e-6, 10)
ops.algorithm('Newton')
ops.integrator('Newmark', 0.5, 0.25)
ops.analysis('Transient')

# Perform dynamic analysis
time = []
displacement = []
velocity = []
acceleration = []
base_reaction = []

stable = 0
current_time = 0.0
    
while stable == 0 and current_time < duration:
    stable = ops.analyze(1, dt)
    current_time = ops.getTime()
    time.append(current_time)
    displacement.append(ops.nodeDisp(2, 1))
    velocity.append(ops.nodeVel(2, 1))
    acceleration.append(ops.nodeAccel(2, 1))
    base_reaction.append(-ops.eleResponse(1, 'force')[0])  # Reaction force
    #base_reaction.append(-k * displacement[-1])  # Reaction force
    #base_reaction.append(ops.nodeResponse(1, 1, 6))  # Reaction force

# Plot results
plt.figure(figsize=(18, 16))

# Displacement
plt.subplot(4, 1, 1)
plt.plot(time, displacement, label='Displacement')
plt.xlabel('Time [s]')
plt.ylabel('Displacement [m]')
plt.title('Displacement Time History')
plt.grid(True)

# Velocity
plt.subplot(4, 1, 2)
plt.plot(time, velocity, label='Velocity', color='orange')
plt.xlabel('Time [s]')
plt.ylabel('Velocity [m/s]')
plt.title('Velocity Time History')
plt.grid(True)

# Acceleration
plt.subplot(4, 1, 3)
plt.plot(time, acceleration, label='Acceleration', color='green')
plt.xlabel('Time [s]')
plt.ylabel('Acceleration [m/s^2]')
plt.title('Acceleration Time History')
plt.grid(True)

# Base Reaction Displacement
plt.subplot(4, 1, 4)
plt.plot(time, base_reaction, label='Base Reaction', color='red')
plt.xlabel('Time [s]')
plt.ylabel('Base Reaction [N]')
plt.title('Base Reaction Time History')
plt.grid(True)

plt.tight_layout()
plt.show()
