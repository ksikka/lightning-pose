from lightning_pose.utils.cropzoom import generate_cropped_csv_file
from tqdm import tqdm

preds_csv = "fuse_outputs/chickadee/pose_{idx}_1.8/image_preds/cropped_CollectedData_merged{new_suffix}.csv/predictions.csv"
bbox_csv = "fuse_outputs/chickadee/single_{idx}/image_preds/CollectedData_merged{new_suffix}.csv/bbox.csv"
out_preds_csv = "fuse_outputs/chickadee/pose_{idx}_1.8/image_preds/cropped_CollectedData_merged{new_suffix}.csv/remapped_predictions.csv"

for idx in tqdm(range(3)):
    for new_suffix in tqdm(["", "_new"]):
        generate_cropped_csv_file(
            input_csv_file=preds_csv.format(new_suffix=new_suffix, idx=idx),
            input_bbox_file=bbox_csv.format(new_suffix=new_suffix, idx=idx),
            output_csv_file=out_preds_csv.format(new_suffix=new_suffix, idx=idx),
            mode="add",
        )
