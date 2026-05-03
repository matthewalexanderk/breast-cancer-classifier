# Breast Cancer Classifier

Breast cancer prediction using classification models on tabular clinical data from the Breast Cancer Wisconsin (Diagnostic) dataset. 

This repository contains a Jupyter notebook that trains and evaluates
Logistic Regression and Random Forest models to predict breast cancer
(malignant vs benign) from clinical features.

Both models were evaluated using metrics such as accuracy and ROC–AUC,
and feature importance was examined to understand which variables
contributed most to the predictions. 

## Results

- **Logistic Regression** achieved an accuracy of 0.98, with precision/recall of 0.98/0.98 for malignant and 0.99/0.99 for benign cases on the test set.
- **Random Forest** achieved an accuracy of 0.96, with precision/recall of 0.95/0.93 for malignant and 0.96/0.97 for benign cases on the test set. 

## Conclusion

In this dataset, tumour size (mean radius in millimetres) is
positively associated with malignancy, with larger tumours more likely
to be classified as malignant. Logistic Regression and Random Forest
models were both shown to be good predictors for tumour type.

## File

- `breast_cancer_prediction_classifier_model.ipynb`: EDA, preprocessing,
  model training, and evaluation.

## Python Learning Game

- `python_learning_game.py`: a gamified, level-based Python learning quest.
- Run it in VS Code (or any terminal) with:
  - `python python_learning_game.py`
- When prompted, type your Python code and finish with a line containing `END`.
  Type `QUIT` to exit.
