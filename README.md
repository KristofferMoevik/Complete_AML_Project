## Project in Advanced Machine Learning
This repository contains all code we used to produce the results given in our report for the project of 3D novelty detection.

# Step 2 - Semantic novelty detection baselines
To replicate our results enter the folder Step_2_and_3_3DOS. Run all the commands in the README.md file in the folder. 
Then run the script train_models.sh and afterwards run the script evaluate_models.sh. The evaluaations of the different models will be in the folder Evaluations.

# Step 3 - Semantic novelty detection analysis
To replicate our results use the scripts follow the steps:
1. Have Step_2_and_3_3DOS as working directory
2. Run all the python scripts in the folder Step_2_and_3_3D_OS/Failure_Analysis/Evaluate and save data.
   These scripts evaluate the different data and saves the data.
3. To vizualise the different failure cases run the scripts in the folder Step_2_and_3_3D_OS/Failure_Analysis/Analyze data.
   The run the script for the model you want to analyze.

# Step 4 - Fine-Tuning free semantic novelty detection
To replicate our results run the notebook Step_4_OpenShape_for_3D_novelty_detection.ipynb.

# Step 5 - Extension
To replicate our quality control extension run the notebooks:
1. Step_5_Detecting_defect_chairs_with_OpenShape.ipynb
2. Step_5_Detecting_defect_chairs_with_PointNet.ipynb
