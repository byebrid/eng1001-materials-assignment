# Materials assignment source code
Team 109, ENG1001, Monash University (2021 Semester 1).

## Quick intro to code
`part2.py` is the main script that was used to determine the most efficient beam design for each different cross-sectional shape and material. `beams.py` simply defines each different cross-section (and also the `Material` class).

There's some file input/output going on, so it may be annoying to rerun this code on another device. However, we'll do our best to make sure you can replicate our results if you want. Specifically,
* We expect a csv file in the same directory as this source code called `part2_table1.csv`. This is literally just a csv version of the given Table 1 in the assignment.
* You should get output files in a subdirectory called `part2_results`. Can't be bothered checking, but you might need to create the subdirectory manually first (but you shouldn't need to manually create any files inside of it.)

The code is neat at times and hideous at others. Enter with caution.

## Setup
We're assuming some basic knowledge of python environments here. Create a virtual environment, and `pip install -r requirements.txt`. Alternatively, just `pip install numpy` as the only other requirements were for actually writing the code.

## Running the code
```
$ python part2.py
```

## Results
Look in the `part2_results` subdirectory for the corresponding csv files.