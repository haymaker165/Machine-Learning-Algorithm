#! python3
"""
Created on Sun Nov 10 11:02:32 2019

Multi Data Type Pipeline using RandomForestClassifier to predict 'Category' field in Financial transaction data
    
Steps:
    1. Import modules
    2. Import dataset and split training & testing data
    3. Build Pipeline to Impute numeric data and Count Vectorize text data
    4. Create GridSearchCV to find best hyperparamters and fit training data to model
    5. Print model performance
    6. Create excel spreadsheet with model's predictions for y target variable (Category)

@author: HM
"""

# Import necessary modules
import os, pandas as pd, datetime, numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import Imputer, FunctionTransformer, StandardScaler
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier

# Ignores Warnings
import warnings
warnings.filterwarnings(action='ignore')

# Changes current working directory to where Transaction file is stored
os.chdir("FILE PATH HERE")

table = pd.read_csv("FILE NAME HERE")

X_data = table[['$ Amount', 'Description']]
Y_data = table['Category']

# Splits using ALL data in transaction table to categorize 'Category' field in data
X_train, X_test, y_train, y_test = train_test_split(X_data,
                                                    Y_data,
                                                    test_size=0.2,
                                                    random_state=22)


# Creates the basic token pattern
# NOTE: Text tokens in vectorizer below decreases accuracy score
TOKENS_BASIC = '\\S+(?=\\s+)'

# Obtains the text data
get_text_data1 = FunctionTransformer(lambda x: x['Description'], validate=False)

# Obtains the numeric data
get_numeric_data = FunctionTransformer(lambda x: x[['$ Amount']], validate=False)

# Creates a FeatureUnion with nested pipeline
# NOTE: ngram_range used to go up to 4 n grams for vectorizing text
process_and_join_features = FeatureUnion(
            transformer_list = [
                ('numeric_features', Pipeline([
                    ('selector', get_numeric_data),
                    ('imputer', Imputer())
                ])),
                ('text_features1', Pipeline([
                    ('selector', get_text_data1),
                    ('vectorizer', CountVectorizer(TOKENS_BASIC, ngram_range=(1,4)))
                ]))
            ]
        )

# Instantiates nested pipeline
pl = Pipeline([
        ('union', process_and_join_features),
#       NOTE: Standard Scalar imported to reduce large variances in data inputs
        ('scaler', StandardScaler(with_mean=False)),
        ('clf', RandomForestClassifier())
    ])

# Creates parameters variable for GridSearchCV function to be used
parameters = {'clf__n_estimators':np.arange(1,5)}

# Use GridSearchCV to find parameters with highest accuracy score
cv = GridSearchCV(pl, param_grid=parameters)

# Fits cv to the training data
cv.fit(X_data, Y_data)
y_pred = cv.predict(X_test)

# Computes and prints accuracy
accuracy = cv.score(X_test, y_test)
print("\nAccuracy on test data: {:.1%}\n".format(accuracy))

# Calculates cross-validation score to compute numpy mean and prints result
cv_scores = cross_val_score(pl, X_data, Y_data, cv=10)
print('\nCV scores: {}'.format(cv_scores))
print('\nCV score mean: {:.1%}'.format(np.mean(cv_scores)))
print('\n')

# Prints best parameters and classification report by each Category within Target Variable
print(cv.best_params_)
print('\n')
print(classification_report(y_test, y_pred))

# --** BELOW CREATES EXCEL SPREADSHEET WITH PREDICTIONS FROM MODEL **--

# Creates Pandas DataFrame of test data with model prediction column
results = pd.DataFrame(X_test)
results['Prediction'] = cv.predict(X_test)

# Joins correct 'Category' data from Y_data var to compare against model prediction
results = results.join(Y_data)

# Creates new Category Classifier Model Prediction spreadsheet and puts in folder
date = datetime.datetime.today().strftime('%m-%d-%Y')

file_name = "FILE LOCATION AND NAME TEMPLATE HERE"

try:
    results.to_excel(file_name)
except PermissionError:
    print('\nFile for ' + date + ' has already been created')
