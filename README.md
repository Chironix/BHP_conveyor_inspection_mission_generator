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

- [x] **CRITICAL**: Replace yaml.load() with Python dictionaries/classes to eliminate security vulnerability and improve performance
- [x] Fixed bugs in generated files (invalid quaternions, template label pollution, incorrect tolerance placement)
- [x] Created proper class hierarchy with PoseStamped encapsulating optional tolerance
- [x] Removed redundant/unused code (PoseHeader, PoseStamped v1, has_anomaly field)
- [ ] Add error handling throughout (missing keys, file operations, invalid configs)

### Medium Priority (Functionality)

- [x] Make the entry point "main.py"
- [ ] All "task" artefacts (which I don't believe are used by the missions at all?) are put into a folder named "artefacts" or something obvious that they are to be deleted or ignored.
- [ ] The scripts are parameterised such that once I find out how many idlers can be inspected in a single image, I can change the parameters and the mission generation script will be appropriate. Currently, the distances between the waypoints is the only variable and I don't want to have to do the math myself in the field.
- [ ] Magic numbers replaced with named constants/config parameters (5.760 spacing, 1.44 offsets, etc.)
- [ ] The naming of the navigation goals and inspection points are relevant to the idler number so that they can be interpreted easily.
- [x] Mission 3 and 4 need to be different.
  - [x] Mission 3 needs to generate two missions; one which returns home and one which goes on to the other end.
  - [x] Mission 4 just stops at the end.
- [x] The missions need to return home to dock after they are completed.
- [ ] Remove the arg parsing in preference for config files.
- [x] Remove the concept of reverse missions.

### Low Priority (Code Organization)

- [x] Extract duplicated orientation-setting logic into reusable function
- [x] Break down large main() function (230+ lines) into smaller, testable functions
- [x] Add docstrings to all functions for field maintainability
- [x] Consider reducing deepcopy usage for performance on long conveyors
- [x] Clean up unused/dead code paths (e.g., main.py:171-173)

### Lowest Priority (Nit Picking)

- [x] Fix double file extension bug (environment_out.yaml.yaml) - args.output should not include .yaml extension
- [x] Fix typo in cli_helpers.py:52 ("evironment" -> "environment")

### Notes

I am concerned that the distance between the rollers will change once when the tunnel changes angle.
How should I change the script to account for this?
Output just the one mission, taking in the start and stop point? I just need to adjust the start and stop offset to account for the discrepency in the positions.
Nah.
Okay, then I will look up the mech drawings now and supply some more config options for the offsets for the change points in the mission.

Something to think about regarding the accuracy of the inspection points.
This is a very long mission.
The mission generator currently takes the waypoints and divides the distance based on the spacing of the idlers.
Really, we know where the idlers will be ahead of time from the mechanical drawings.
But, when recording the map, unless it is perfectly accurate localisation, we may have a situation where the robot thinks the tunnel is longer or shorter than it is and so the idlers gradually go out of frame.
So, if I change it such that I use the waypoints to set the elevation gain and vector only, but then the script generates the same length of inspection points and creates new waypoints for what the tunnel SHOULD be doing, then the waypoints and the slam map will be out of whack.
I guess it depends on how far out of whack the map and reality is?
For now, I will just continue with how we set the waypoints at the verteces and then hope it all works out...
I'll get the waypoint positions from the mechanical drawings and test it all out in sim.


Generate just the list of tasks?
Then, I can have another entry point for turning the tasks into a mission which returns back to the docking station?
This would imply that I run the thing 4 times.
I am thinking of doing this because of the whole forward and reverse missions.
Do we need reverse missions?
No.

So, the tasks files can go.

The mission generator uses this config_env.yaml file currently.
There are "start" and "end" positions.
I should get the waypoint.yaml file and then have the config read the positions from there.
That way, I can also
Actually wait, I don't need to do that.
It would just be reading another file to get the same info and have all the same function arguments.
