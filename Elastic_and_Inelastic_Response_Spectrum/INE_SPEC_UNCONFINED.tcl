#puts "       >>   IN THE NAME OF ALLAH  <<     "
#puts "    INELASTIC RESPONSE SPECTRUM ANALYSIS      "
set tStart [clock clicks -milliseconds]
for {set i 1} {$i <= 1000} {incr i} {# loop of mass increment
# SET UP ----------------------------------------------------------------------------
# units: N, mm, sec
wipe;					# clear memory of all past model definitions
file mkdir SPECTRUM/INE_SPEC_UNCONFINED; 				# create data directory
model BasicBuilder -ndm 2 -ndf 3;		# Define the model builder, ndm=#dimension, ndf=#dofs


# define GEOMETRY ========================================================
# define section geometry
set B 200; #Width of Column Section
set Ela 23500;# Modulus of Elasticity of Section
set Le 3000;# Length of Column
set Dpr 0.02;#Damping ratio
set RZD 16;# Column Rebar Size Diameter
set Ma [expr 0.2*$i];
set A [expr $B*$B];# area of Section
set I [expr ($B*$B*$B*$B)/12];# Moment Intria of Section
set Ke [expr (3*$Ela*$I)/pow($Le,3)];# Sitffness of Structure
set PERIOD [expr  2*3.1415*sqrt($Ma/$Ke)];# Sitffness of Structure
 puts "INCREMENT: $i -> PERIOD: $PERIOD"


# nodal coordinates:
node 1 0 0;			# node#, X, Y
node 2 0 $Le 		

# Single point constraints -- Boundary Conditions
fix 1 1 1 1; 			# node DX DY RZ

# nodal masses:
mass 2 $Ma  1e-9 0.;		# node#, Mx My Mz, Mass=Weight/g, neglect rotational inertia at nodes

# Define ELEMENTS & SECTIONS ========================================================
set ColSecTag 1;			# assign a tag number to the column section	
# define section geometry
set coverCol 25.;			# Column cover to reinforcing steel NA.
set numBarsCol 8;			# number of longitudinal-reinforcement bars in column. (symmetric top & bot)
set barAreaCol [expr (3.1415*$RZD*$RZD)/4];	# area of longitudinal-reinforcement bars
# MATERIAL parameters -------------------------------------------------------------------
set IDconcU 1; 			# material ID tag -- unconfined cover concrete
set IDreinf 2; 				# material ID tag -- reinforcement
# nominal concrete compressive strength
set fc -25.; 				# CONCRETE Compressive Strength (+Tension, -Compression)
set Ec [expr 4700*sqrt(-$fc)]; 		# Concrete Elastic Modulus (the term in sqr root needs to be in psi
# unconfined concrete
set fc1U 		$fc;			# UNCONFINED concrete (todeschini parabolic model), maximum stress
set eps1U	-0.003;			# strain at maximum strength of unconfined concrete
set fc2U 		[expr 0.2*$fc1U];		# ultimate stress
set eps2U	-0.01;			# strain at ultimate stress
set lambda 0.1;				# ratio between unloading slope at $eps2 and initial slope $Ec
# tensile-strength properties
set ftU [expr -0.55*$fc1U];			# tensile strength +tension
set Ets [expr $ftU/0.002];			# tension softening stiffness
# -----------
set Fy 4000;				# STEEL yield stress
set Es 200000.;				# modulus of steel
set Bs 0.01;				# strain-hardening ratio 
set R0 18;				# control the transition from elastic to plastic branches
set cR1 0.925;				# control the transition from elastic to plastic branches
set cR2 0.15;				# control the transition from elastic to plastic branches
uniaxialMaterial Concrete02 $IDconcU $fc1U $eps1U $fc2U $eps2U $lambda $ftU $Ets;	# build cover concrete (unconfined)
uniaxialMaterial Steel02 $IDreinf $Fy $Es $Bs $R0 $cR1 $cR2;				# build reinforcement material

# FIBER SECTION properties -------------------------------------------------------------
# symmetric section
#                        y
#                        ^
#                        |     
#             ---------------------     --   --
#             |   o     o     o    |     |    -- cover
#             |                       |     |
#             |                       |     |
#    z <--- |          +           |     H
#             |                       |     |
#             |                       |     |
#             |   o     o     o    |     |    -- cover
#             ---------------------     --   --
#             |-------- B --------|
#
# RC section: 
   set coverY [expr $B/2.0];	# The distance from the section z-axis to the edge of the cover concrete -- outer edge of cover concrete
   set coverZ [expr $B/2.0];	# The distance from the section y-axis to the edge of the cover concrete -- outer edge of cover concrete
   set coreY [expr $coverY-$coverCol]
   set coreZ [expr $coverZ-$coverCol]
   set nfY 16;			# number of fibers for concrete in y-direction
   set nfZ 4;			# number of fibers for concrete in z-direction
   section fiberSec $ColSecTag   {;	# Define the fiber section
	patch quadr $IDconcU $nfZ $nfY -$coverY $coverZ -$coverY -$coverZ $coverY -$coverZ $coverY $coverZ; 	# Define the concrete patch
	layer straight $IDreinf $numBarsCol $barAreaCol -$coreY $coreZ -$coreY -$coreZ;	# top layer reinfocement
	layer straight $IDreinf $numBarsCol $barAreaCol  $coreY $coreZ  $coreY -$coreZ;	# bottom layer reinforcement
    };

# define geometric transformation: performs a linear geometric transformation of beam stiffness and resisting force from the basic system to the global-coordinate system
set ColTransfTag 1; 			# associate a tag to column transformation
geomTransf Linear $ColTransfTag  ; 	

# element connectivity:
set numIntgrPts 5;								# number of integration points for force-based element
element nonlinearBeamColumn 1 1 2 $numIntgrPts $ColSecTag $ColTransfTag;	# self-explanatory when using variables

# Define RECORDERS ========================================================
recorder EnvelopeNode -file SPECTRUM/INE_SPEC_UNCONFINED/DFree_$i.txt -time -node 2 -dof 1 disp;			# displacements of free nodes
recorder EnvelopeNode -file SPECTRUM/INE_SPEC_UNCONFINED/VFree_$i.txt -time -node 2 -dof 1 vel;			        # vel of free nodes
recorder EnvelopeNode -file SPECTRUM/INE_SPEC_UNCONFINED/AFree_$i.txt -time -node 2 -dof 1 accel;			# accel of free nodes
recorder EnvelopeNode -file SPECTRUM/INE_SPEC_UNCONFINED/RBase_$i.txt -time -node 1 -dof 1 reaction;			# support reaction
# define GRAVITY ========================================================
pattern Plain 1 Linear {
   load 2 0 0 0
}

# Gravity-analysis parameters -- load-controlled static analysis
set Tol 1.0e-8;			# convergence tolerance for test
constraints Plain;     		# how it handles boundary conditions
numberer Plain;			# renumber dof's to minimize band-width (optimization), if you want to
system BandGeneral;		# how to store and solve the system of equations in the analysis
test NormDispIncr $Tol 6 ; 		# determine if convergence has been achieved at the end of an iteration step
algorithm Newton;			# use Newton's solution algorithm: updates tangent stiffness at every iteration
set NstepGravity 10;  		# apply gravity in 10 steps
set DGravity [expr 1./$NstepGravity]; 	# first load increment;
integrator LoadControl $DGravity;	# determine the next time step for an analysis
analysis Static;			# define type of analysis static or transient
analyze $NstepGravity;		# apply gravity
# ------------------------------------------------- maintain constant gravity loads and reset time to zero
loadConst -time 0.0

puts "Model Built"

# DYNAMIC EQ ANALYSIS ========================================================
# Uniform Earthquake ground motion (uniform acceleration input at all support nodes)
set GMdirection 1;				# ground-motion direction
set GMfile "Northridge_EQ.acc" ;			# ground-motion filenames
set GMfact 1;				# ground-motion scaling factor

# set up ground-motion-analysis parameters
set DtAnalysis 0.01;	# time-step Dt for lateral analysis
set TmaxAnalysis	[expr 10.];	# maximum duration of ground-motion analysis -- should be 50*$sec

# DYNAMIC ANALYSIS PARAMETERS
constraints Transformation ; 
numberer Plain
system SparseGeneral -piv
set Tol 1.e-8;                        # Convergence Test: tolerance
set maxNumIter 10;                # Convergence Test: maximum number of iterations that will be performed before "failure to converge" is returned
set printFlag 0;                # Convergence Test: flag used to print information on convergence (optional)        # 1: print information on each step; 
set TestType EnergyIncr;	# Convergence-test type
test $TestType $Tol $maxNumIter $printFlag;
set algorithmType ModifiedNewton 
algorithm $algorithmType;        
set NewmarkGamma 0.5;	# Newmark-integrator gamma parameter (also HHT)
set NewmarkBeta 0.25;	# Newmark-integrator beta parameter
integrator Newmark $NewmarkGamma $NewmarkBeta 


analysis Transient

# define DAMPING========================================================
# apply Rayleigh DAMPING from $xDamp
# D=$alphaM*M + $betaKcurr*Kcurrent + $betaKcomm*KlastCommit + $beatKinit*$Kinitial
set xDamp $Dpr;				# 2% damping ratio
set lambda [eigen 1]; 			# eigenvalue mode 1
set omega [expr pow($lambda,0.5)];
set alphaM 0.;				# M-prop. damping; D = alphaM*M
set betaKcurr 0.;         			# K-proportional damping;      +beatKcurr*KCurrent
set betaKcomm [expr 2.*$xDamp/($omega)];   	# K-prop. damping parameter;   +betaKcomm*KlastCommitt
set betaKinit 0.;         			# initial-stiffness proportional damping      +beatKinit*Kini
# define damping
rayleigh $alphaM $betaKcurr $betaKinit $betaKcomm; 				# RAYLEIGH damping

#  ---------------------------------    perform Dynamic Ground-Motion Analysis
# Uniform EXCITATION: acceleration input
set IDloadTag 400;			# load tag
set dt 0.01;			# time step for input ground motion
set GMfatt 1.0;			# data in input file is in g Unifts -- ACCELERATION TH
set AccelSeries "Series -dt $dt -filePath $GMfile -factor  $GMfatt";			# time series information
pattern UniformExcitation  $IDloadTag  $GMdirection -accel  $AccelSeries  ;		# create Unifform excitation

set Nsteps 5736;#[expr int($TmaxAnalysis/$DtAnalysis)];
set ok [analyze $Nsteps $DtAnalysis];			# actually perform analysis; returns ok=0 if analysis was successful

if {$ok != 0} {      ;					# if analysis was not successful.
	# change some analysis parameters to achieve convergence
	# performance is slower inside this loop
	#    Time-controlled analysis
	set ok 0;
	set controlTime [getTime];
	while {$controlTime < $TmaxAnalysis && $ok == 0} {
		set ok [analyze 1 $DtAnalysis]
		set controlTime [getTime]
		set ok [analyze 1 $DtAnalysis]
		if {$ok != 0} {
			puts "Trying Newton with Initial Tangent .."
			test NormDispIncr   $Tol 1000  0
			algorithm Newton -initial
			set ok [analyze 1 $DtAnalysis]
			test $TestType $Tol $maxNumIter  0
			algorithm $algorithmType
		}
		if {$ok != 0} {
			puts "Trying Broyden .."
			algorithm Broyden 8
			set ok [analyze 1 $DtAnalysis]
			algorithm $algorithmType
		}
		if {$ok != 0} {
			puts "Trying NewtonWithLineSearch .."
			algorithm NewtonLineSearch .8
			set ok [analyze 1 $DtAnalysis]
			algorithm $algorithmType
		}
	}
};      # end if ok !0


puts "Ground Motion Done. End Time: [getTime]"
}
set tEnd [clock clicks -milliseconds]
set duration [expr $tEnd-$tStart]
puts "Anaysis Duration: $duration"
