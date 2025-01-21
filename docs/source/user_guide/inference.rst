.. _inference:

#########
Inference
#########

When you install lightning pose via pip from source, it will also install a
command-line tool ``litpose``.  The ``litpose predict`` subcommand is used to
run model inference on new data. It expects the location of your model,
the location of the data you want to predict on, and it will output
predictions to a subdirectory of the model directory.

The command-line tool is a wrapper around our python library. For an example
of how to predict on new data programmatically, see its source code 
under ``lightning_pose/cli/main.py``.

Inference on new videos using the command-line
==============================================

The ``litpose predict``

.. code-block:: shell

    python scripts/predict_new_vids.py --config-path=<PATH/TO/YOUR/CONFIGS/DIR> --config-name=<CONFIG_NAME.yaml>

.. note::

  Videos *must* be mp4 files that use the h.264 codec; see more information in the
  :ref:`FAQs<faq_video_formats>`.


In order to use this script more generally, you need to update several config fields:

#. ``eval.hydra_paths``: path to models to use for prediction
#. ``eval.test_videos_directory``: path to a `directory` containing videos to run inference on
#. ``eval.save_vids_after_training``: if ``true``, the script will also save a copy of the full video with model predictions overlaid.

The results will be stored in the model directory.

As with training, you either directly edit your config file and run:

Inference with sample dataset
=============================

If you trained a model on the sample dataset included with the lightning pose repository,
you can run the following command from inside the ``lightning-pose`` directory
(make sure you have activated your conda environment):

.. code-block:: shell

    litpose predict <model_dir> data/mirror-mouse-example/videos