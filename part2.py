import csv
import numpy as np
from beams import IBeam, RHSBeam, CHSBeam, Material

##################### DEFINING CONSTANTS FOR USE LATER ON #####################
# SI prefixes for clearer unit conversion, so we don't have to constantly worry
# about units when calculating derived properties!
MILLI = 10**(-3)
KILO = 10**3
MEGA = 10**6
GIGA = 10**9

# Indices to access data from numpy array (note that the first column of
# material names gets dropped)
YIELD_STRESS, MODULUS, ELONGATION, DENSITY, PRICE, ENERGY = range(
    0, 6)

# Defining variables related to shape/loading of beam
length = 2000 * MILLI  # [m]
loading = 24 * KILO  # [N]
max_breadth = 30 * MILLI  # [m]
max_height = 100 * MILLI  # [m]

# Define our "step-size" for each dimension of every beam. Brief only asks for
# mm precision, so that's what we'll use!
step_size = 1 * MILLI  # [m]

##################### READING MATERIAL DATA FROM CSV FILE #####################
# Reading Table 1 csv file into numpy array (ignoring headers)
with open("part2_table1.csv", "r") as csvfile:
    reader = csv.reader(csvfile)

    rows = [row for row in reader]
    data = np.array(rows[1:])
    # Take out materials so we can cast everything else to floats
    materials = data[:, 0]
    # Convert data from strings to floats
    data = data[:, 1:].astype(float)

# Converting units in data array to avoid headaches later
data[:, YIELD_STRESS] *= MEGA  # [MPa] -> [Pa]
data[:, MODULUS] *= GIGA  # [GPa] -> [Pa]
data[:, ELONGATION] /= 100  # [%] to [actual number]
data[:, DENSITY] *= 10**3  # [tonnes] -> [kg]
data[:, ENERGY] *= MEGA  # [MJ/kg] -> [J/kg]

### DEFINING NESTED FOR LOOPS FOR EACH CROSS-SECTION TO DETERMINE BEST BEAM ###


def get_best_I_beam(material: Material):
    best_I_beam = None

    for b in np.arange(step_size, max_breadth + step_size, step_size):
        for h in np.arange(step_size, max_height + step_size, step_size):
            for tw in np.arange(step_size, b + step_size, step_size):
                for tf in np.arange(step_size, h/2 + step_size, step_size):
                    beam = IBeam(material, length, b, h, tw, tf)
                    best_I_beam = beam.get_new_best_beam(loading, best_I_beam)

    return best_I_beam


def get_best_RHS_beam(material: Material):
    best_RHS_beam = None

    for b in np.arange(step_size, max_breadth + step_size, step_size):
        for h in np.arange(step_size, max_height + step_size, step_size):
            # Walls' thickness is constrained by overall breadth/height of beam
            min_dimension = min(b, h)
            for t in np.arange(step_size, min_dimension / 2 + step_size, step_size):
                beam = RHSBeam(material, length, b, h, t)
                best_RHS_beam = beam.get_new_best_beam(loading, best_RHS_beam)

    return best_RHS_beam


def get_best_CHS_beam(material: Material):
    best_CHS_beam = None
    min_dimension = min(max_breadth, max_height)

    # We obviously lose a lot of our possible envelope by using a circular
    # cross-section. Restrict to minimum dimensions (should be 30mm).
    for r in np.arange(step_size, min_dimension / 2 + step_size, step_size):
        for t in np.arange(step_size, r + step_size, step_size):
            beam = CHSBeam(material, length, r, t)
            best_CHS_beam = beam.get_new_best_beam(loading, best_CHS_beam)

    return best_CHS_beam


### GOING THROUGH EVERY MATERIAL, FINDING BEST BEAMS FOR EACH CROSS-SECTION ###
# Arrays to store best beams for each material (note we only add materials if
# they are actually suitable, otherwise we ignore them. This leads to CHS array
# only having one element!)
best_I_beams = []
best_RHS_beams = []
best_CHS_beams = []
for i, material_name in enumerate(materials):
    print(f"MATERIAL: {material_name}")

    # Getting properties of this material
    yield_stress = data[i, YIELD_STRESS]
    modulus = data[i, MODULUS]
    elongation = data[i, ELONGATION]
    density = data[i, DENSITY]
    price = data[i, PRICE]
    energy_density = data[i, ENERGY]

    # Creating Material class
    material = Material(material_name, yield_stress, modulus,
                        elongation, density, price, energy_density)

    # Checking I-beams
    best_I_beam = get_best_I_beam(material)
    if best_I_beam is not None:
        best_I_beams.append(best_I_beam)
        print("    Found suitable I-beam!")
    else:
        print("    No suitable I-beam!")

    # Checking RHS beams
    best_RHS_beam = get_best_RHS_beam(material)
    if best_RHS_beam is not None:
        best_RHS_beams.append(best_RHS_beam)
        print("    Found suitable RHS-beam!")
    else:
        print("    No suitable RHS-beam!")

    # Checking CHS beams
    best_CHS_beam = get_best_CHS_beam(material)
    if best_CHS_beam is not None:
        best_CHS_beams.append(best_CHS_beam)
        print("    Found suitable CHS-beam!")
    else:
        print("    No suitable CHS-beam!")

########################## WRITING RESULTS TO FILES ##########################
# NOTE: We do some unit conversions here so the results are easier to read in
# the csv files/spreadsheets!

# Writing I-beams to file
with open("part2_results/I_beams.csv", "w+") as csvfile:
    writer = csv.writer(csvfile, dialect="excel")

    headers = ("Material", "Area [mm^2]", "Breadth [mm]", "Height [mm]", "Web thickness [mm]", "Flange thickness [mm]",
               "I_xx [mm^4]", "I_yy [mm^4]", "Buckling load [kN]", "Squash load [kN]", "Strain", "Embodied energy [MJ]", "Cost [$]", "Embodied energy cost [$]", "Total cost [$]")
    writer.writerow(headers)

    for beam in best_I_beams:
        row = (beam.material.name, beam.area/MILLI**2, beam.b/MILLI, beam.h/MILLI, beam.tw/MILLI, beam.tf/MILLI, beam.second_moment_of_area_xx/MILLI**4,
               beam.second_moment_of_area_yy/MILLI**4, beam.buckling_load/KILO, beam.squash_load/KILO, beam.get_strain(loading), beam.total_embodied_energy/MEGA, beam.cost, beam.embodied_energy_cost, beam.total_cost)
        writer.writerow(row)

# Writing RHS-beams to file
with open("part2_results/RHS_beams.csv", "w+") as csvfile:
    writer = csv.writer(csvfile, dialect="excel")

    headers = ("Material", "Area [mm^2]", "Breadth [mm]", "Height [mm]", "Wall thickness [mm]",
               "I_xx [mm^4]", "I_yy [mm^4]", "Buckling load [kN]", "Squash load [kN]", "Strain", "Embodied energy [MJ]", "Cost [$]", "Embodied energy cost [$]", "Total cost [$]")
    writer.writerow(headers)

    for beam in best_RHS_beams:
        row = (beam.material.name, beam.area/MILLI**2, beam.b/MILLI, beam.h/MILLI, beam.t/MILLI, beam.second_moment_of_area_xx/MILLI**4,
               beam.second_moment_of_area_yy/MILLI**4, beam.buckling_load/KILO, beam.squash_load/KILO, beam.get_strain(loading), beam.total_embodied_energy/MEGA, beam.cost, beam.embodied_energy_cost, beam.total_cost)
        writer.writerow(row)

# Writing CHS-beams to file
with open("part2_results/CHS_beams.csv", "w+") as csvfile:
    writer = csv.writer(csvfile, dialect="excel")

    headers = ("Material", "Area [mm^2]", "Radius [mm]", "Wall thickness [mm]",
               "I_xx [mm^4]", "I_yy [mm^4]", "Buckling load [kN]", "Squash load [kN]", "Strain", "Cost [$]", "Embodied energy [MJ]", "Embodied energy cost [$]", "Total cost [$]", )
    writer.writerow(headers)

    for beam in best_CHS_beams:
        row = (beam.material.name, beam.area/MILLI**2, beam.r/MILLI, beam.t/MILLI, beam.second_moment_of_area_xx/MILLI**4,
               beam.second_moment_of_area_yy/MILLI**4, beam.buckling_load/KILO, beam.squash_load/KILO, beam.get_strain(loading), beam.cost, beam.total_embodied_energy/MEGA, beam.embodied_energy_cost, beam.total_cost)
        writer.writerow(row)
