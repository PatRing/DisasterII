import sys
import joblib
import nltk
import pandas as pd
from sqlalchemy import create_engine
import string
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score

import pickle
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report


nltk.download('stopwords')
STOP_WORDS = nltk.corpus.stopwords.words("english")
lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()
PUNCTUATION_TABLE = str.maketrans('', '', string.punctuation)

def load_data(database_filepath):
    engine = create_engine('sqlite:///' + database_filepath)
    df = pd.read_sql_table('table', engine)
    engine.dispose()

    category_names = df.columns[4:]

    X = df[['message']].values[:, 0]
    y = df[category_names].values

    return X, y, category_names


def tokenize(text):
    """Basic tokenizer that removes punctuation and stopwords then lemmatizes
    Args:
        text (string): input message to tokenize
    Returns:
        tokens (list): list of cleaned tokens in the message
    """
    # normalize case and remove punctuation
    text = text.translate(PUNCTUATION_TABLE).lower()

    # tokenize text
    tokens = nltk.word_tokenize(text)

    # lemmatize and remove stop words
    return [lemmatizer.lemmatize(word) for word in tokens
                                                    if word not in STOP_WORDS]



def build_model():
    """Returns the GridSearchCV object to be used as the model
    Args:
        None
    Returns:
        cv (scikit-learn GridSearchCV): Grid search model object
    """

    clf = RandomForestClassifier(n_estimators=10)

    # The pipeline has tfidf, dimensionality reduction, and classifier
    pipeline = Pipeline([
                    ('tfidf', TfidfVectorizer(tokenizer=tokenize)),
                    ('best', TruncatedSVD(n_components=100)),
                    ('clf', MultiOutputClassifier(clf))
                      ])

    
    param_grid = {
        'tfidf__max_df': [0.8, 1.0]
    }

    #Initialize a gridsearch object that is parallelized
    cv = GridSearchCV(pipeline, param_grid, cv=2, verbose=10, n_jobs=-1)

    return cv


def evaluate_model(model, X_test, Y_test, category_names):
     Y_pred = model.predict(X_test)   
     for i in range(0, len(category_names)):
        print(category_names[i])
        print("\tAccuracy: {:.4f}\t\t% Precision: {:.4f}\t\t% Recall: {:.4f}\t\t% F1_score: {:.4f}".format(
            accuracy_score(Y_test[:, i], Y_pred[:, i]),
            precision_score(Y_test[:, i], Y_pred[:, i], average='weighted'),
            recall_score(Y_test[:, i], Y_pred[:, i], average='weighted'),
            f1_score(Y_test[:, i], Y_pred[:, i], average='weighted')
))

def save_model(model, model_filepath):
    
    pickle.dump(model, open(model_filepath, 'wb'))
   

def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names  = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()