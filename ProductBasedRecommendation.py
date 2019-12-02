# -*- coding: utf-8 -*-
"""
Created on Mon Aug  5 08:29:10 2019

@author: ML team
"""
from flask import Flask, render_template,request, jsonify
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler,MinMaxScaler
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.cluster import KMeans
from collections import defaultdict
from sklearn.metrics.pairwise import euclidean_distances
from itertools import islice
import pickle
import re
import operator
import sys
sys.path.insert(0,"/var/www/FLASKAPPS/helloworldapp/")

def dict_lookup(key, dictionary):
    if key in dictionary: 
        return dictionary[key]
    for value in dictionary.values():
        if isinstance(value, dict):
            dict_val = dict_lookup(key, value)
            if dict_val is not None: 
                return dict_val
    return None

with open('var/www/FLASKAPPS/helloworldapp/labelencoder_Category_prod.pickle', 'rb') as handle:
    labelencoder_Category = pickle.load(handle)

with open('var/www/FLASKAPPS/helloworldapp/labelencoder_brand_prod.pickle', 'rb') as handle:
    labelencoder_brand = pickle.load(handle)

with open('var/www/FLASKAPPS/helloworldapp/labelencoder_OS_prod.pickle', 'rb') as handle:
    labelencoder_OS = pickle.load(handle)

with open('var/www/FLASKAPPS/helloworldapp/labelencoder_CPU_prod.pickle', 'rb') as handle:
    labelencoder_CPU = pickle.load(handle)

with open('var/www/FLASKAPPS/helloworldapp/labelencoder_wireless_type_prod.pickle', 'rb') as handle:
    labelencoder_wireless_type = pickle.load(handle)

with open('var/www/FLASKAPPS/helloworldapp/standardScaler_X_prod.pickle', 'rb') as handle:
    standardScaler_X = pickle.load(handle)

with open(var/www/FLASKAPPS/helloworldapp/'clusterDF_prod.pickle', 'rb') as handle:
    clusterDF = pickle.load(handle)

with open('var/www/FLASKAPPS/helloworldapp/AllProducts.pickle', 'rb') as handle:
    AllProdDF = pickle.load(handle)

def is_compatible(inpProdID, candidateProd):
    
    inpProdDF = AllProdDF[AllProdDF.Product_ID == inpProdID]
    candidateProdDF = AllProdDF[AllProdDF.Product_ID == candidateProd]
    compatible = False
    if str(candidateProdDF.Compatible_devices.values[0]) == str(inpProdDF.Compatible_devices.values[0]):
        compatible = True
    #elif str(candidateProdDF.Category.values[0]).lower() == 'mobile cover' and \
    #str(inpProdDF.Category.values[0]).lower() == 'mobile cover':
    #    compatible = True       
    elif str(candidateProdDF.Compatible_devices.values[0]) == 'all devices':
        compatible = True
    elif str(candidateProdDF.Compatible_devices.values[0]) == 'all android devices' and \
    (('android' in (str(inpProdDF.OS.values[0])).lower()) or \
     ('apple' != str(inpProdDF.Brand.values[0]).lower()) or \
     (str(inpProdDF.Compatible_devices.values[0]) == 'all devices') ):
        compatible = True
    elif str(candidateProdDF.Compatible_devices.values[0]) == str(inpProdDF.Brand.values[0]).lower():
        compatible = True       
    elif inpProdID in str(candidateProdDF.Compatible_devices.values[0]):
        compatible = True
    return compatible         
        
def get_individual_recommendation(prodID, topN = 10):
    prodExists = False
    cluster = -1
    dfProd = clusterDF[clusterDF.Product_ID == prodID]
    if len(dfProd) > 0:
        prodExists = True
        cluster = dfProd.Cluster.values[0]

    RankedRecommendations = []
    if prodExists:
        df = clusterDF.loc[clusterDF.Cluster == cluster]
        dfExceptProd = df.loc[df.Product_ID != prodID]
        dfProd = dfProd.append(dfExceptProd)
        simDF = dfProd.drop(columns = ['Product_ID','Model', 'Cluster'])
        X = simDF[:].values
        X[:,0]=labelencoder_Category.transform(X[:,0])
        X[:,1]=labelencoder_brand.transform(X[:,1])
        X[:,5]=labelencoder_OS.transform(X[:,5])
        X[:,6]=labelencoder_CPU.transform(X[:,6])
        X[:,14]=labelencoder_wireless_type.transform(X[:,14])
        X = standardScaler_X.transform(X)
        distance = []
        for i in range(X.shape[0]):
            dist = euclidean_distances([X[0]], [X[i]])
            distance.append(dist[0][0])
        dfWithDistance = dfProd.copy()
        dfWithDistance['Distance'] = distance
        dfWithDistance.sort_values(by = ['Distance'], ascending = True, inplace = True)
        dfWithDistance = dfWithDistance[1:]
        distance = 0.0
        Rank = topN
        FirstProd = True
        for index, row in dfWithDistance.iterrows():
            if is_compatible(prodID, row['Product_ID']):
                #print(row['Brand'], row['Model'])
                if FirstProd or float(row['Distance']) == distance:
                    RankedRecommendations.append((row['Product_ID'], Rank))
                    distance = float(row['Distance'])
                    FirstProd = False
                else:
                    Rank = Rank - 1
                    RankedRecommendations.append((row['Product_ID'], Rank))
                    distance = float(row['Distance'])
            if Rank <= 0:
                break
    RankedRecommendations = RankedRecommendations[:topN] 
    return RankedRecommendations

#To support call from the flask app with request data
def recommend_similar_products():
    data = request.get_json(force=True)
    print('Product Similarity Request Data:',data)
    ProductID = dict_lookup('ProductId', data)
    TopN = dict_lookup('topN', data)
    if not TopN:
        TopN = 10
    TopN = int(TopN)
    ProductAttributes = dict_lookup('ProductAttributes', data)
    Items = ""
    Ranks = ""
    if ProductID:
        print('Input for Product Similarity Recommendation:', ProductID, TopN)
        prods = re.findall(r"[\w-]+", ProductID)
        prodSimRankedRecs = []
        for prod in prods:
            prodSimRankedRecs += get_individual_recommendation(prod, TopN)
        ConsolidatedDF = pd.DataFrame(prodSimRankedRecs, columns = ['ProductID', 'Rank'])
        ConsolidatedDF = ConsolidatedDF.sort_values(by = ConsolidatedDF.columns[1],  ascending=False)
        ConsolidatedDF = ConsolidatedDF[ConsolidatedDF["ProductID"].isin(prods) == False]  
        ConsolidatedDF = ConsolidatedDF.drop_duplicates(subset = ['ProductID'], keep = 'first')
        ConsolidatedDF = ConsolidatedDF[:TopN]
        RankedRecs = []
        for index, row in ConsolidatedDF.iterrows():
            RankedRecs.append((row['ProductID'], row['Rank']))
        print('Outpt of Product Similarity Recommendation:', RankedRecs)
    
        for pID, Rnk in RankedRecs:
            Items = Items + str(pID) + "|"
            Ranks = Ranks + str(Rnk) + "|"
    
    return jsonify(ProductID = Items, Rank = Ranks)