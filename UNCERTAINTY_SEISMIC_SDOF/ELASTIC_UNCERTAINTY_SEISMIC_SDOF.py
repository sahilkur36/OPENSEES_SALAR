###########################################################################################################
#                                         IN THE NAME OF ALLAH                                            #
#                    DYNAMIC RESPONSE ANALYSIS OF A SINGLE-DEGREE-OF-FREEDOM (SDOF)                       #
#           STRUCTURE UNDER SEISMIC LOADING WITH UNCERTAINTY USING MONTE CARLO SIMULATION:                #
#                 INCORPORATING BETA PROBABILITY DISTRIBUTION FOR STOCHASTIC PARAMETERS                   #
#---------------------------------------------------------------------------------------------------------#
# This program models and analyzes the dynamic response of a single-degree-of-freedom (SDOF) structural   #
# system subjected to seismic accelerations while incorporating uncertainties in structural properties.   #
# The framework supports researchers and engineers in assessing the probabilistic performance of          #
# structures under seismic excitation, emphasizing the role of uncertainty in seismic response and        #
# design.                                                                                                 #
#---------------------------------------------------------------------------------------------------------#
#                          THIS PROGRAM WRITTEN BY SALAR DELAVAR GHASHGHAEI (QASHQAI)                     #
#                                   EMAIL: salar.d.ghashghaei@gmail.com                                   #
###########################################################################################################
#
# Objectives:
# 1. Stochastic Parameter Modeling:
#    - Use Beta probability distribution functions to generate random values for:
#        Stiffness (k)
#        Mass (m)
#        Damping ratio (ζ)
#        Seismic accelerations
#    - Provide a statistical representation of uncertainties in structural properties and loading conditions.
#
# 2. Structural Model Development:
#    - Build an SDOF system in OpenSeesPy with stochastic parameters:
#        * Variable stiffness, mass, and damping ratio
#    - Apply seismic accelerations as dynamic input to the system.
#
# 3. Monte Carlo Simulation:
#    - Perform transient dynamic analysis iteratively over numerous realizations of stochastic parameters.
#    - Capture variability in system behavior and response.
#
# 4. Response Analysis:
#    - Monitor and record critical system responses:
#        Displacement, velocity, and acceleration
#        Base reaction forces over time
#    - Aggregate simulation results to compute probabilistic metrics of structural response.
#
# 5. Visualization and Statistical Assessment:
#    - Generate graphical representations for enhanced insights:
#        Histograms and boxplots for distributions of maximum displacement, velocity, acceleration, and base reaction forces.
#        Time-history plots illustrating system response dynamics for representative cases.
#
# 6. Seismic Safety Assessment:
#    - Evaluate seismic safety using simulation data by training a Random Forest Classifier to
#        predict system safety under varying conditions.
#
# 7. Correlation Analysis:
#    - Create a heatmap to visualize correlations between key parameters and responses.
#
# 8. Multiple Regression Modeling:
#    - Develop a regression model to estimate system responses based on stochastic parameters.
#
# 9. Machine Learning: Long Short-Term Memory (LSTM):
#    - Implement LSTM networks to predict dynamic responses over time for advanced probabilistic modeling.
#
# 10. Reliability Analysis:
#    - Perform reliability assessments of base reactions and element capacities to quantify structural safety margins.
#
# 11. Markov Chain Model:
#    - Structural damage analysis by evaluating displacement
#
#---------------------------------------------------------------------------------------------------------
# This framework integrates stochastic modeling, dynamic simulation, and machine learning to provide a   
# robust tool for evaluating seismic performance and ensuring structural reliability under uncertainty.   


#------------------------------------------------------------------------------------------------
import time as ti
import numpy as np
import openseespy.opensees as ops
import matplotlib.pyplot as plt
import SALAR_MATH as S01
import Analysis_Function as S02
import MARKOV_CHAIN as S03

# The selection of alpha and beta coefficients in the beta probability distribution is crucial.
# In uncertainty analysis, careful consideration must also be given to the numerical interval (maximum and minimum) and the alpha and beta coefficients.
#------------------------------------------------------------------------------------------------
# Define parameters (units: m, N)
NUM_SIM = 6000                                   # Total number for simulation
Ea = S01.BETA_PDF(2.0e3, 2.1e3, 1, 2, NUM_SIM)   # [N/m^2] Spring material Elastic modulus
AREA = S01.BETA_PDF(0.01, 0.012, 1, 2, NUM_SIM)  # [m^2] Spring Section Area
LENGTH = S01.BETA_PDF(9.9, 10.1, 2, 1, NUM_SIM)  # [m] Spring Length
K = (Ea * AREA) / LENGTH                         # [N/m] Stiffness of the structure
M = S01.BETA_PDF(1500.0, 1700.0, 2, 1, NUM_SIM)  # [kg] Mass of the structure
DR = S01.BETA_PDF(0.01, 0.03, 1, 1, NUM_SIM)     # Damping ratio

duration = 15.0  # [s] Total simulation duration
dt = 0.01        # [s] Time step
#------------------------------------------------------------------------------------------------
# Define Analysis Properties
MAX_ITERATIONS = 1000000   # Convergence iteration for test
MAX_TOLERANCE = 1.0e-10    # Convergence tolerance for test
#------------------------------------------------------------------------------------------------
# SPRING STIFFNESS PROPERTIES
S01.HISROGRAM_BOXPLOT(Ea, HISTO_COLOR='pink', LABEL='Spring material Elastic modulus')
S01.HISROGRAM_BOXPLOT(AREA, HISTO_COLOR='lightblue', LABEL='Spring Section Area')
S01.HISROGRAM_BOXPLOT(LENGTH, HISTO_COLOR='lime', LABEL='Spring Length')
S01.HISROGRAM_BOXPLOT(K, HISTO_COLOR='brown', LABEL='Spring Stiffness')
# SPRING MASS AND DAMPING RATIO PROPERTIES
S01.HISROGRAM_BOXPLOT(M, HISTO_COLOR='yellow', LABEL='Mass')
S01.HISROGRAM_BOXPLOT(DR, HISTO_COLOR='cyan', LABEL='Damping Ratio')
#------------------------------------------------------------------------------------------------
### OpenSees Function
def ANALYSIS_SDOF(i):
    # Initialize OpenSees model
    ops.wipe()
    ops.model('basic', '-ndm', 1, '-ndf', 1)
    GMfact = 9.81 # [m/s^2] standard acceleration of gravity or standard acceleration 
        
    # Define nodes
    ops.node(1, 0.0)  # Fixed base
    ops.node(2, 0.0)  # Mass node
        
    # Define boundary conditions
    ops.fix(1, 1)
    
    # Define mass
    ops.mass(2, M[i])
        
    # Natural frequency [rad/s]
    wn = (K[i] / M[i]) ** 0.5
    # Damping coefficient [Ns/m]
    C = 2 * wn * M[i] * DR[i]
        
    # Define material properties
    ops.uniaxialMaterial('Elastic', 1, K[i])
    # Define materials for structural damper
    ops.uniaxialMaterial('Elastic', 2, 0.0, C)
        
    # Define element
    ops.element('zeroLength', 1, 1, 2, '-mat', 1, 2, '-dir', 1, 1)  # DOF[1] LATERAL SPRING
    
    # Apply seismic accelerations    
    # Define time series for input motion (Acceleration time history)
    ops.timeSeries('Path', 1, '-dt', 0.01, '-filePath', f'Ground_Acceleration_{i+1}.txt', '-factor', GMfact) # SEISMIC-X
        
    # Define load patterns
    # pattern UniformExcitation $patternTag $dof -accel $tsTag <-vel0 $vel0> <-fact $cFact>
    ops.pattern('UniformExcitation', 200, 1, '-accel', 1) # SEISMIC-X
    
    # Output data
    #ops.recorder('Node', '-file', f"DTH_DYN_{i}.txt",'-time', '-node', 2, '-dof', 1, 'disp')     # Displacement Time History Node 2
    #ops.recorder('Node', '-file', f"VTH_DYN_{i}.txt",'-time', '-node', 2, '-dof', 1, 'vel')      # Velocity Time History Node 2
    #ops.recorder('Node', '-file', f"ATH_DYN_{i}.txt",'-time', '-node', 2, '-dof', 1, 'accel')    # Acceleration Time History Node 2
    #ops.recorder('Node', '-file', f"BTH_DYN_{i}.txt",'-time', '-node', 1, '-dof', 1, 'reaction') # Base Reaction Time History Node 1
        
    # Set analysis parameters
    ops.constraints('Plain')
    ops.numberer('Plain')
    ops.system('BandGeneral')
    ops.test('NormDispIncr', MAX_TOLERANCE, MAX_ITERATIONS)
    ops.algorithm('Newton')
    ops.integrator('Newmark', 0.5, 0.25)
    ops.analysis('Transient')
        
    # Re-run dynamic analysis with new loading
    time = []
    displacement = []
    velocity = []
    acceleration = []
    base_reaction = []
        
    stable = 0
    current_time = 0.0
    
    while stable == 0 and current_time < duration:
        stable = ops.analyze(1, dt)
        S02.ANALYSIS(stable, 1, MAX_TOLERANCE, MAX_ITERATIONS) # CHECK THE ANALYSIS
        current_time = ops.getTime()
        time.append(current_time)
        displacement.append(ops.nodeDisp(2, 1))
        velocity.append(ops.nodeVel(2, 1))
        acceleration.append(ops.nodeAccel(2, 1))
        base_reaction.append(-ops.eleResponse(1, 'force')[0])  # Reaction force
        #KE = np.abs(base_reaction[-1]) / displacement[-1]
        
    ops.wipe()
    return time, displacement, velocity, acceleration, base_reaction
    
#------------------------------------------------------------------------------------------------
# Analysis Durations:
starttime = ti.process_time()

# Initialize lists to store max values
max_time = []
max_displacement = []
max_velocity = []
max_acceleration = []
max_base_reaction = []
# NUM_SIM is the number of simulations
for i in range(NUM_SIM):
    time, displacement, velocity, acceleration, base_reaction = ANALYSIS_SDOF(i)
    # Calculate and store the max absolute values
    max_time.append(np.max(np.abs(time)))
    max_displacement.append(np.max(np.abs(displacement)))
    max_velocity.append(np.max(np.abs(velocity)))
    max_acceleration.append(np.max(np.abs(acceleration)))
    max_base_reaction.append(np.max(np.abs(base_reaction)))
    print(f'STEP {i + 1} DONE') 

totaltime = ti.process_time() - starttime
print(f'\nTotal time (s): {totaltime:.4f} \n\n') 
#------------------------------------------------------------------------------------------------
# Print the last results
print("Maximum Absolute Values Across Simulations:")
print("Time:", max_time[-1])
print("Displacement:", max_displacement[-1])
print("Velocity:", max_velocity[-1])
print("Acceleration:", max_acceleration[-1])
print("Base Reaction:", max_base_reaction[-1])
#------------------------------------------------------------------------------------------------
S01.HISROGRAM_BOXPLOT(max_displacement, HISTO_COLOR='blue', LABEL='Displacement')
S01.HISROGRAM_BOXPLOT(max_velocity, HISTO_COLOR='purple', LABEL='Velocity')
S01.HISROGRAM_BOXPLOT(max_acceleration, HISTO_COLOR='green', LABEL='Acceleration')
S01.HISROGRAM_BOXPLOT(max_base_reaction, HISTO_COLOR='gold', LABEL='Base Reaction')
#------------------------------------------------------------------------------------------------
# Compute the Cumulative Maximum Absolute Value of Last Analysis Data
def MAX_ABS(X):
    import numpy as np
    X = np.asarray(X)  # Convert input to a numpy array for faster operations
    X_MAX = np.zeros_like(X)  # Initialize an array to store cumulative max values
    X_MAX[0] = np.abs(X[0])  # Set the first value

    # Compute cumulative maximum absolute values
    for i in range(1, len(X)):
        X_MAX[i] = max(X_MAX[i-1], np.abs(X[i]))
    
    return X_MAX  

DISP_Z = MAX_ABS(displacement)  
VELO_Z = MAX_ABS(velocity) 
ACCE_Z = MAX_ABS(acceleration) 
BASE_Z = MAX_ABS(base_reaction) 

plt.figure(1, figsize=(8, 6))
plt.plot(time, displacement, color='blue', linewidth=2)
plt.plot(time, DISP_Z, color='red', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Displacement [m]')
plt.title(f'Time vs Displacement - MAX. ABS: {DISP_Z[-1]}')
plt.grid()
plt.show()

plt.figure(2, figsize=(8, 6))
plt.plot(time, velocity, color='blue', linewidth=2)
plt.plot(time, VELO_Z, color='red', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Velocity [m/s]')
plt.title(f'Time vs Velocity - MAX. ABS: {VELO_Z[-1]}')
plt.grid()
plt.show()

plt.figure(3, figsize=(8, 6))
plt.plot(time, acceleration, color='blue', linewidth=2)
plt.plot(time, ACCE_Z, color='red', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Acceleration [m/s^2]')
plt.title(f'Time vs Acceleration - MAX. ABS: {ACCE_Z[-1]}')
plt.grid()
plt.show()

plt.figure(4, figsize=(8, 6))
plt.plot(time, base_reaction, color='blue', linewidth=2)
plt.plot(time, BASE_Z, color='red', linewidth=2)
plt.xlabel('Time [s]')
plt.ylabel('Base-reaction [N]')
plt.title(f'Time vs Base-reaction - MAX. ABS: {BASE_Z[-1]}')
plt.grid()
plt.show()
#------------------------------------------------------------------------------------------------
XLABEL = 'Displacement'
YLABEL = 'Base Reaction'
TITLE = f'{YLABEL} and {XLABEL} scatter chart'
COLOR = 'orange'
X = max_displacement
Y = max_base_reaction
S01.PLOT_SCATTER(X, Y , XLABEL, YLABEL, TITLE, COLOR, LOG = 0, ORDER = 1)

# CLUSTER DATA
S01.CLUSTER_DATA(X, Y, XLABEL, YLABEL, MAX_CLUSTERS=3)
#------------------------------------------------------------------------------------------------
XLABEL = 'Velocity'
YLABEL = 'Base Reaction'
TITLE = f'{YLABEL} and {XLABEL} scatter chart'
COLOR = 'cyan'
X = max_velocity
Y = max_base_reaction
S01.PLOT_SCATTER(X, Y , XLABEL, YLABEL, TITLE, COLOR, LOG = 0, ORDER = 1)

# CLUSTER DATA
S01.CLUSTER_DATA(X, Y, XLABEL, YLABEL, MAX_CLUSTERS=3)
#------------------------------------------------------------------------------------------------
XLABEL = 'Acceleration'
YLABEL = 'Base Reaction'
TITLE = f'{YLABEL} and {XLABEL} scatter chart'
COLOR = 'lime'
X = max_acceleration
Y = max_base_reaction
S01.PLOT_SCATTER(X, Y , XLABEL, YLABEL, TITLE, COLOR, LOG = 0, ORDER = 1)

# CLUSTER DATA
S01.CLUSTER_DATA(X, Y, XLABEL, YLABEL, MAX_CLUSTERS=3)
#------------------------------------------------------------------------------------------------
# PLOT THE TIME-HISTORY
S01.PLOT_TIME_HISTORY(time, displacement, velocity, acceleration, base_reaction)
#------------------------------------------------------------------------------------------------
# RANDOM FOREST ANALYSIS
"""
This code predicts the seismic safety of a structure using simulation data by training a Random Forest Classifier to
 classify whether the system is "safe" or "unsafe" based on features like maximum displacement, velocity, acceleration,
 and base reaction. A regression model is also trained to estimate safety likelihood. It evaluates model performance using
 metrics like classification accuracy, mean squared error, and R² score. Additionally, it identifies key features influencing
 safety through feature importance analysis. The tool aids in seismic risk assessment, structural optimization, and understanding
 critical safety parameters.
"""

import pandas as pd

data = {
    'Max_displacement': max_displacement,
    'Max_velocity': max_velocity,
    'Max_acceleration': max_acceleration,
    'Max_Base_Reaction': max_base_reaction,
    'Damping_Ratio': DR,
}


# Convert to DataFrame
df = pd.DataFrame(data)
#print(df)
S01.RANDOM_FOREST(df)
#------------------------------------------------------------------------------------------------
# PLOT HEATMAP FOR CORRELATION 
S01.PLOT_HEATMAP(df)
#------------------------------------------------------------------------------------------------
# MULTIPLE REGRESSION MODEL
S01.MULTIPLE_REGRESSION(df) 
#------------------------------------------------------------------------------------------------
# MACHINE LEARNING: LONG SHORT-TREM MEMERY (LSTM) METHOD
x = max_displacement 
y = max_acceleration 
look_back = int(NUM_SIM * 0.5)
ITERATION = 200
XLABEL = 'Max Displacement'
YLABEL = 'Max Acceleration'
S01.PREDICT_LSTM(x, y, look_back, ITERATION, XLABEL, YLABEL)
#------------------------------------------------------------------------------------------------
# PERFORM RELIABILITY ANALYSIS FOR BASE REACTION AND ELEMENT CAPACITY
mean_capacity = np.mean(Ea * AREA)    # Mean Element Elastic Capacity
std_dev_capacity = np.std(Ea * AREA)  # Std Element Elastic Capacity
num_sim = NUM_SIM
S01.RELIABILITY_ANALYSIS(max_base_reaction, num_sim, mean_capacity, std_dev_capacity)
#------------------------------------------------------------------------------------------------
# MARKOV CHAIN MODEl (structural damage analysis by evaluating displacement)
FILE_TF = False         # Indicate whether to read data from a file or use provided data
file_path = None        # Not used when 'file_tf' is False
DATA = max_displacement # If not using a file, replace None with a NumPy array of data

S03.MARKOV_CHAIN(FILE_TF, file_path, DATA)
#------------------------------------------------------------------------------------------------