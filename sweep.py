from lightning_sdk import Studio, Machine
import re

# Start the studio
# studio = Studio()
studio = Studio(name="lightning-pose", teamspace="lp-dev", org="zuckerman-institute")

# Define the machine to run the jobs on

# Use the jobs plugin
jobs_plugin = studio.installed_plugins["jobs"]

detector_train_commands = """
litpose train chickadee.yaml --output_dir outputs/chickadee/single_0 --overrides training.train_frames=500
litpose train chickadee.yaml --output_dir outputs/chickadee/single_1 --overrides training.train_frames=500 training.rng_seed_data_pt=1 dali.general.seed=1234561
litpose train chickadee.yaml --output_dir outputs/chickadee/single_2 --overrides training.train_frames=500 training.rng_seed_data_pt=2 dali.general.seed=1234562
"""

detector_crop_commands = """
litpose predict outputs/chickadee/single_0 CollectedData_merged.csv CollectedData_merged_new.csv --detector_mode
litpose predict outputs/chickadee/single_1 CollectedData_merged.csv CollectedData_merged_new.csv --detector_mode
litpose predict outputs/chickadee/single_2 CollectedData_merged.csv CollectedData_merged_new.csv --detector_mode
"""

pose_train_commands = """
litpose train chickadee.yaml --output_dir outputs/chickadee/pose_0_1.8 --overrides training.train_frames=500 --detector_model=outputs/chickadee/single_0
litpose train chickadee.yaml --output_dir outputs/chickadee/pose_1_1.8 --overrides training.train_frames=500 training.rng_seed_data_pt=1 dali.general.seed=1234561 --detector_model=outputs/chickadee/single_1
litpose train chickadee.yaml --output_dir outputs/chickadee/pose_2_1.8 --overrides training.train_frames=500 training.rng_seed_data_pt=2 dali.general.seed=1234562 --detector_model=outputs/chickadee/single_2
"""

pose_ood_commands = """
litpose predict outputs/chickadee/pose_0_1.8 outputs/chickadee/single_0/image_preds/CollectedData_merged_new.csv/cropped_CollectedData_merged_new.csv
litpose predict outputs/chickadee/pose_1_1.8 outputs/chickadee/single_1/image_preds/CollectedData_merged_new.csv/cropped_CollectedData_merged_new.csv
litpose predict outputs/chickadee/pose_2_1.8 outputs/chickadee/single_2/image_preds/CollectedData_merged_new.csv/cropped_CollectedData_merged_new.csv
"""

do = [detector_crop_commands, pose_train_commands, pose_ood_commands]
do2 = []

for commands in do:
  commands = commands.splitlines()
  # Filter out empty lines
  commands = [line for line in commands if line.strip()]
  do2.append(commands)


dry_run = False

for command_list in zip(*do2): 
    #m = re.search(r"model_name='(.*?)'", i)
    m = re.search(r"outputs/chickadee/(.*?) ", command_list[0])
    job_name = m.group(1) + " train and ood predict"

    print(job_name)


    #machine = Machine.T4_X_4
    machine = Machine.L4
    #machine = Machine.CPU
    command = "cd lightning-pose\n"+'\n'.join(command_list)
    print(command)

    if dry_run:
        continue

    job = jobs_plugin.run(
        command=command,
        machine=machine,
        name=job_name
    )
    #print(f"Submitted job {job.name} with ID {job.id}")
    print(f"Submitted job {job.name}")
