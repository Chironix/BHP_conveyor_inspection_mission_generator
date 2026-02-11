# ANYmal Environment Generation utility

This utility application is for generating an inspection mission of a long straight conveyor belt.
Due to the length of the belt, and thus the number of inspections that must take place, creating this mission manually would be a nightmare.
The utility app helps streamline the process such that it can be run in the field.

## Output and Limitations

The output will be 4 missions that run in a particular way such that the robot always returns back to the beginning, except for the final mission which ends at the other end of the tunnel.
The missions will consist of walking to the segment to inspect, then taking images of clusters of idlers at once.

This utility can only be used to make inspections of the top idlers.

## Usage

### Environment Init with the Robot (On the day)

1. Record the map.
    1. Have roller door open, robot in the portal, PTZ facing down the length.
    1. Then turn it around and face the lidar down the tunnel for the rest of the mapping so that I can hide in the shadow.
    1. This will make the map have x in the positive direction.
1. Copy the environment file and the waypoints file from the NPC into this folder.
1. Pack the robot up, take it back to the office, and get the batteries onto charge.

### Creating the Environment & Missions

Do all of this in the sim whilst the robot is charging.

1. Fill the config_env.yaml with the coordinates of the waypoints.
1. Run in the folder python3 generate_straight_environment_and_missions_FW_RV.py.

Done, find missions in the generated_tasks/ folder and the environment under enviornment_out.yaml.

## TODO / Next Steps

### High Priority (Code Quality & Security)

- [ ] **CRITICAL**: Replace yaml.load() with Python dictionaries in environment_utils.py and mission_utils.py to eliminate security vulnerability and improve performance
- [ ] Fix double file extension bug (environment_out.yaml.yaml) - args.output should not include .yaml extension
- [ ] Add error handling throughout (missing keys, file operations, invalid configs)
- [ ] Fix typo in cli_helpers.py:52 ("evironment" -> "environment")

### Medium Priority (Functionality)

- [x] Make the entry point "main.py"
- [ ] All "task" artefacts (which I don't believe are used by the missions at all?) are put into a folder named "artefacts" or something obvious that they are to be deleted or ignored.
- [ ] The scripts are parameterised such that once I find out how many idlers can be inspected in a single image, I can change the parameters and the mission generation script will be appropriate. Currently, the distances between the waypoints is the only variable and I don't want to have to do the math myself in the field.
- [ ] Magic numbers replaced with named constants/config parameters (5.760 spacing, 1.44 offsets, etc.)
- [ ] The naming of the navigation goals and inspection points are relevant to the idler number so that they can be interpreted easily.
- [ ] Mission 3 and 4 need to be different.
  - [ ] Mission 3 needs to generate two missions; one which returns home and one which goes on to the other end.
  - [ ] Mission 4 just stops at the end.
- [ ] The missions need to return home to dock after they are completed.

### Low Priority (Code Organization)

- [ ] Extract duplicated orientation-setting logic into reusable function
- [ ] Break down large main() function (230+ lines) into smaller, testable functions
- [ ] Add docstrings to all functions for field maintainability
- [ ] Consider reducing deepcopy usage for performance on long conveyors
- [ ] Clean up unused/dead code paths (e.g., main.py:171-173)

### Notes

I am concerned that the distance between the rollers will change once when the tunnel changes angle.
How should I change the script to account for this?
Output just the one mission, taking in the start and stop point? I just need to adjust the start and stop offset to account for the discrepency in the positions.
Nah.
Okay, then I will look up the mech drawings now and supply some more config options for the offsets for the change points in the mission.
