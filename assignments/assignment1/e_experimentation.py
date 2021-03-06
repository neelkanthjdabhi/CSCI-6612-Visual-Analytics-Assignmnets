import collections
import itertools
from pathlib import Path
from typing import Union, Optional
from enum import Enum

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

from assignments.assignment1.b_data_profile import *
from assignments.assignment1.c_data_cleaning import *
from assignments.assignment1.d_data_encoding import *
from assignments.assignment1.a_load_file import read_dataset


##############################################
# Example(s). Read the comments in the following method(s)
##############################################


def process_iris_dataset() -> pd.DataFrame:
    """
    In this example, I call the methods you should have implemented in the other files
    to read and preprocess the iris dataset. This dataset is simple, and only has 4 columns:
    three numeric and one categorical. Depending on what I want to do in the future, I may want
    to transform these columns in other things (for example, I could transform a numeric column
    into a categorical one by splitting the number into bins, similar to how a histogram creates bins
    to be shown as a bar chart).

    In my case, what I want to do is to *remove missing numbers*, replacing them with valid ones,
    and *delete outliers* rows altogether (I could have decided to do something else, and this decision
    will be on you depending on what you'll do with the data afterwords, e.g. what machine learning
    algorithm you'll use). I will also standardize the numeric columns, create a new column with the average
    distance between the three numeric column and convert the categorical column to a onehot-encoding format.

    :return: A dataframe with no missing values, no outliers and onehotencoded categorical columns
    """
    df = read_dataset(Path('..', '..', 'iris.csv'))
    numeric_columns = get_numeric_columns(df)
    categorical_columns = get_text_categorical_columns(df)

    for nc in numeric_columns:
        df = fix_outliers(df, nc)
        df = fix_nans(df, nc)
        df.loc[:, nc] = standardize_column(df.loc[:, nc])

    distances = pd.DataFrame()
    for nc_combination in list(itertools.combinations(numeric_columns, 2)):
        distances[str(nc_combination)] = calculate_numeric_distance(df.loc[:, nc_combination[0]],
                                                                    df.loc[:, nc_combination[1]],
                                                                    DistanceMetric.EUCLIDEAN).values

    df['numeric_mean'] = distances.mean(axis=1)

    for cc in categorical_columns:
        ohe = generate_one_hot_encoder(df.loc[:, cc])
        df = replace_with_one_hot_encoder(df, cc, ohe, list(ohe.get_feature_names()))

    return df


##############################################
# Implement all the below methods
# All methods should be dataset-independent, using only the methods done in the assignment
# so far and pandas/numpy/sklearn for the operations
##############################################
def process_iris_dataset_again() -> pd.DataFrame:
    """
    Consider the example above and once again perform a preprocessing and cleaning of the iris dataset.
    This time, use normalization for the numeric columns and use label_encoder for the categorical column.
    Also, for this example, consider that all petal_widths should be between 0.0 and 1.0, replace the wong_values
    of that column with the mean of that column. Also include a new (binary) column called "large_sepal_lenght"
    saying whether the row's sepal_length is larger (true) or not (false) than 5.0
    :return: A dataframe with the above conditions.
    """

    df = read_dataset(Path('..', '..', 'iris.csv'))
    numeric_columns = get_numeric_columns(df)
    categorical_columns = get_text_categorical_columns(df)

    # Filling wrong values with mean
    df.loc[df['petal_width'] > 1.0, 'petal_width'] = df['petal_width'].mean()
    df.loc[df['petal_width'] < 0.0, 'petal_width'] = df['petal_width'].mean()

    # Assigning binary col conditionally before the normalization
    # happens as normalization will bring values between 0 & 1
    df['large_sepal_lenght'] = df["sepal_length"] > 5.0

    # Fixing data before normalization as we need scaled data
    for nc in numeric_columns:
        df = fix_outliers(df, nc)
        df = fix_nans(df, nc)
        df.loc[:, nc] = normalize_column(df.loc[:, nc])

    # Label Encoding
    for cc in categorical_columns:
        le = generate_label_encoder(df.loc[:, cc])
        df = replace_with_label_encoder(df, cc, le)

    return df


def process_amazon_video_game_dataset():
    """
    Now use the rating_Video_Games dataset following these rules:
    1. The rating has to be between 1.0 and 5.0
    2. Time should be converted from milliseconds to datetime.datetime format
    3. For the future use of this data, I don't care about who voted what, I only want the average rating per product,
        therefore replace the user column by counting how many ratings each product had (which should be a column called count),
        and the average rating (as the "review" column).
    :return: A dataframe with the above conditions. The columns at the end should be: asin,review,time,count
    """

    df = read_dataset(Path('..', '..', 'ratings_Video_Games.csv'))

    # 1  The rating has to be between 1.0 and 5.0
    df = df[df['review'].between(1, 5)]

    # 2 Time should be converted from milliseconds to datetime.datetime format
    df['time'] = pd.to_datetime(df['time'], unit='ms')

    """
    # 3 Group by asin, counting non zero as review is between 1 and 5, 
        taken the latest time as it gives when user last rated any product 
    """
    review_counts = df.groupby(by='asin', as_index=False).agg(
        {'user': np.count_nonzero, 'review': np.mean, 'time': np.max})
    review_counts = review_counts.rename(columns={'user': 'count'})

    return review_counts


def process_amazon_video_game_dataset_again():
    """
    Now use the rating_Video_Games dataset following these rules (the third rule changed, and is more open-ended):
    1. The rating has to be between 1.0 and 5.0, drop any rows not following this rule
    2. Time should be converted from milliseconds to datetime.datetime format
    3. For the future use of this data, I just want to know more about the users, therefore show me how many reviews each user has,
        and a statistical analysis of each user (average, median, std, etc..., each as its own row)
    :return: A dataframe with the above conditions.
    """

    df = read_dataset(Path('..', '..', 'ratings_Video_Games.csv'))

    # 1  The rating has to be between 1.0 and 5.0
    df = df.drop(df[(df['review'] < 1.0) & (df['review'] > 5.0)].index)

    # 2 Time should be converted from milliseconds to datetime.datetime format
    df['time'] = pd.to_datetime(df['time'], unit='ms')

    """
    3.1 asin : Grouping by user and counting asin value to get number of reviews
    3.2 review : Counting number of reviews, review mean, review median, review std from column review 
    3.3 time : min shows users first review, max shows users last review
    """
    df = df.groupby(by='user', as_index=False) \
        .agg({'asin': np.count_nonzero,
              'review': ['count', np.mean, np.median, np.std], 'time': [np.min, np.max]}).fillna(0)

    return df


def process_life_expectancy_dataset():
    """
    Now use the life_expectancy_years and geography datasets following these rules:
    1. The life expectancy dataset has missing values and outliers. Fix them.
    2. The geography dataset has problems with unicode letters. Make sure your code is handling it properly.
    3. Change the format of life expectancy, so that instead of one row with all 28 years, the data has 28 rows, one for each year,
        and with a column "year" with the year and a column "value" with the original value
    4. Merge (or more specifically, join) the two datasets with the common column being the country name (be careful with wrong values here)
    5. Drop all columns except country, continent, year, value and latitude (in this hypothetical example, we wish to analyse differences
        between southern and northern hemisphere)
    6. Change the latitude column from numerical to categorical (north vs south) and pass it though a label_encoder
    7. Change the continent column to a one_hot_encoder version of it
    :return: A dataframe with the above conditions.
    """
    df = read_dataset(Path('..', '..', 'life_expectancy_years.csv'))

    df = df.T
    # removing the country if more than 50% of it's data is nan, it is better to just remove the data then replacing
    # it with mean or any other value.
    df = df.loc[:, df.isnull().mean() < .5]
    df.reset_index(level=0, inplace=True)

    # considering zeroth row as header after transposing
    new_header = df.iloc[0]
    df = df[1:]
    df.reset_index(level=0, inplace=True)
    x = ['index']
    x.extend(new_header)
    df.columns = x

    # handling outliers before moving further
    numeric_columns = get_numeric_columns(df)
    for nc in numeric_columns:
        df = fix_outliers(df, nc)

    # Making sure that we are reading csv in UTF-8 format
    df_geo = pd.read_csv('../../geography.csv', encoding='utf-8')
    df_geo = df_geo.rename(columns={'name': 'country'})

    # Handling outliers and nans before joining Geo Data with life expectancy
    text_categorical_columns = get_text_categorical_columns(df_geo)
    for tcc in text_categorical_columns:
        df_geo = fix_outliers(df_geo, tcc)
        df_geo = fix_nans(df_geo, tcc)

    # melting life expectancy data
    df = df.drop(['index'], axis=1)
    df1 = pd.melt(df, id_vars=['country'])
    df1 = df1.rename(columns={'country': 'year', 'variable': 'country'})

    # merging two dataframes : df_geo(with geographic data) and df(life_expectancy_data)
    df_merged = pd.merge(left=df1, right=df_geo, left_on='country', right_on='country')

    # Dropping all columns except country, continent, year, value and latitude
    # eight_regions as continent because it gives more accurate position of country on the globe
    df_merged = df_merged[['country', 'value', 'eight_regions', 'year', 'Latitude']]
    df_merged = df_merged.rename(columns={'eight_regions': 'continent'})

    # Changing the latitude column from numerical to categorical
    # if the latitude value is positive country is in north hemisphere, else in south hemisphere
    df_merged["Latitude"] = np.where(df_merged['Latitude'] >= 0, 'north', 'south')

    # label encoding of Latitude
    le = generate_label_encoder(df_merged['Latitude'])
    df_le_encoded = replace_with_label_encoder(df_merged, 'Latitude', le)

    # one hot encoding of continent
    ohe = generate_one_hot_encoder(df_merged['continent'])
    df_oh_encoded = replace_with_one_hot_encoder(df_le_encoded, 'continent', ohe, list(ohe.get_feature_names()))

    return df_oh_encoded


if __name__ == "__main__":
    assert process_iris_dataset() is not None
    assert process_iris_dataset_again() is not None
    assert process_amazon_video_game_dataset() is not None
    assert process_amazon_video_game_dataset_again() is not None
    assert process_life_expectancy_dataset() is not None
