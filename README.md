# ANYmal Environment Generation utility

This utility application is for generating an inspection mission of a long straight conveyor belt.
Due to the length of the belt, and thus the number of inspections that must take place, creating this mission manually would be a nightmare.
The utility app helps streamline the process such that it can be run in the field.

## Output and Limitations

The output will be 4 missions that run in a particular way such that the robot always returns back to the beginning, except for the final mission which ends at the other end of the tunnel.
The missions will consist of walking to the segment to inspect, then taking images of clusters of idlers at once.

This utility can only be used to make the top idler inspections.

## Usage

### Environment Init with the Robot (On the day)

1. Record the map.
    1. Have roller door open, robot in the portal, PTZ facing down the length.
    1. Then turn it around and face the lidar down the tunnel for the rest of the mapping so that I can hide in the shadow.
    1. This will make the map have x in the positive direction.
1. Copy the environment file and the waypoints file from the NPC into this folder.
1. Pack the robot up, take it back to the office, and get the batteries onto charge.

Practice generating the missions and the waypoints and things.
When on site, after recording the map, can do the rest in sim to tweak and adjust things. Don't need to be at the front of the tunnel all day just doing that.
Can go back to the office to recharge the batteries whilst doing this tweaking.

### Creating the Environment & Missions

Do all of this in the sim whilst the robot is charging.

1. Fill the config_env.yaml with the coordinates of the waypoints.
1. Run in the folder python3 generate_straight_environment_and_missions_FW_RV.py.

Done, find missions in the generated_tasks/ folder and the environment under enviornment_out.yaml.

## TODO / Next Steps

- [ ] Make the entry point "main.py"
- [ ] All "task" artefacts (which I don't believe are used by the missions at all?) are put into a folder named "artefacts" or something obvious that they are to be deleted or ignored.
- [ ] The output environment file is named something else lol
- [ ] The scripts are parameterised such that once I find out how many idlers can be inspected in a single image, I can change the parameters and the mission generation script will be appropriate. Currently, the distances between the waypoints is the only variable and I don't want to have to do the math myself in the field.
- [ ] The naming of the navigation goals and inspection points are relevant to the idler number so that they can be interpreted easily.
