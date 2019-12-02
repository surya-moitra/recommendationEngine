# -*- coding: utf-8 -*-
"""
Created on Sat Jun 15 23:21:56 2019

@author: sreens
"""
userdetails_filename = 'User_Demographic_data.csv'
useritem_file_name = 'PredictedResultCategoryOLD.csv'
encoding="latin-1"

# Importing the libraries
from flask import Flask, render_template,request, jsonify
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.cluster import KMeans
from collections import defaultdict
from sklearn.metrics.pairwise import euclidean_distances
from itertools import islice
import pickle
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


with open('var/www/FLASKAPPS/helloworldapp/dictofLabelEncodersUser.pickle', 'rb') as handle:
    LabelEncoderObj = pickle.load(handle)
with open('var/www/FLASKAPPS/helloworldapp/standardScalerUser.pickle', 'rb') as handle:
    standardScaler_X = pickle.load(handle)
with open('var/www/FLASKAPPS/helloworldapp/knnusermodelUser.pickle', 'rb') as handle:
    kmeans = pickle.load(handle)
with open('var/www/FLASKAPPS/helloworldapp/clusterDFUser.pickle', 'rb') as handle:
    dflist = pickle.load(handle)
with open('var/www/FLASKAPPS/helloworldapp/useritemdictUser.pickle', 'rb') as handle:
    useritemdict = pickle.load(handle)
with open('var/www/FLASKAPPS/helloworldapp/popularItemsUser.pickle', 'rb') as handle:
    popular_items = pickle.load(handle)

def recommend_products():
    data = request.get_json(force=True)
    print('User Similarity Request Data:', data)
    AccountID = dict_lookup('AccountId', data)
    ProductID = dict_lookup('ProductId', data)
    TopN = dict_lookup('topN', data)
    if not TopN:
        TopN = 10
    TopN = int(TopN)
    AccountAttributes = dict_lookup('AccountAttributes', data)
    Items = ""
    Ranks = ""
    if AccountID:
        print('Input User Similarity Recommendation:', AccountID, TopN)
        userExists = False
        cluster = -1
        recommendations = []
        for index, df in enumerate(dflist):
            dfUser = df[df.Account_Id == AccountID]
            if len(dfUser) > 0:
                userExists = True
                cluster = index
                break
        if not userExists:
            '''
            state  = state.lower()
            Account_type = Account_type.lower()
            dfTest = pd.DataFrame([[state, Account_type, 0.0]], columns = ['State','Account Type', 'NetSpend'])
            encoderColumnState  = LabelEncoderObj['State']
            dfTest.State = encoderColumnState.transform(dfTest.State)
            encoderColumnAccType  = LabelEncoderObj['Account Type']
            dfTest['Account Type'] = encoderColumnAccType.transform(dfTest['Account Type'])
            			
            # Create the input dataframe
            XTest = dfTest[:].values
            XTest = standardScaler_X.transform(XTest)
            yTest = kmeans.predict(XTest)
            cluster = yTest[0]
            '''
            return recommendations
		
        dfCluster= dflist[cluster]
        if userExists:
            dfTest = dfCluster[dfCluster.Account_Id == AccountID]
            dfTest = dfTest.drop(columns = ['Account_Id', 'Cluster'])
            dfTest.State =dfTest.State.apply(lambda x: x.lower())
            dfTest['Account Type'] =dfTest['Account Type'].apply(lambda x: x.lower())
            dfCluster = dfCluster[dfCluster.Account_Id != AccountID]
            encoderColumnState  = LabelEncoderObj['State']
            dfTest.State = encoderColumnState.transform(dfTest.State)
            encoderColumnAccType  = LabelEncoderObj['Account Type']
            dfTest['Account Type'] = encoderColumnAccType.transform(dfTest['Account Type'])
            			
            XTest = dfTest[:].values
            XTest = standardScaler_X.transform(XTest)

        dfLocal = dfCluster.drop(columns = ['Account_Id', 'Cluster'])
        encoderColumnState  = LabelEncoderObj['State']
        dfLocal.State = encoderColumnState.transform(dfLocal.State)
        encoderColumnAccType  = LabelEncoderObj['Account Type']
        dfLocal['Account Type'] = encoderColumnAccType.transform(dfLocal['Account Type'])
        XDelta = dfLocal[:].values
        XDelta = standardScaler_X.transform(XDelta)
        newArray = np.append(XTest, XDelta, axis = 0)
		
        distance = []
        for i in range(newArray.shape[0]):
            dist = euclidean_distances([newArray[0]], [newArray[i]])
            distance.append(dist[0][0])
		
        dfClusterwithdist = dfCluster 
        dfClusterwithdist['Distance'] = distance[1:]
        dfClusterwithdist.sort_values(by = ['Distance'], ascending = True, inplace = True)
        dfClusterwithdist = dfClusterwithdist[dfClusterwithdist.NetSpend > 0.0]
        dfClusterwithdist = dfClusterwithdist[:1]
		
        similarUsersProducts = {}
        for index, row in dfClusterwithdist.iterrows():
            for prodId in useritemdict[row['Account_Id']]:
                if prodId not in useritemdict[AccountID]:
                    similarUsersProducts[prodId] = TopN
		
        popularProducts = popular_items[cluster]
        priorPopularity = popularProducts[0][1]
        popularProductsinCluster = {}
        Rank = TopN
        for prod, value in popularProducts:
            if prod not in useritemdict[AccountID]:
                if priorPopularity == value:
                    popularProductsinCluster[prod] = Rank
                    priorPopularity = value 
                else:
                    Rank = Rank-1
                    popularProductsinCluster[prod] = Rank
                    priorPopularity = value
                if Rank < 1:
                    break
		
        consolidatedProducts = {}
        for product, value in similarUsersProducts.items():
            if product in consolidatedProducts:
                if value > consolidatedProducts[product]:
                    consolidatedProducts[product] = value
            else:
                consolidatedProducts[product] = value
        for product, value in popularProductsinCluster.items():
            if product in consolidatedProducts:
                if value > consolidatedProducts[product]:
                    consolidatedProducts[product] = value
            else:
                consolidatedProducts[product] = value

        RankedProds = sorted(consolidatedProducts.items() , key=lambda x: x[1], reverse = True)
        RankedProds = RankedProds[0:TopN]
        print('Outpt User Similarity Recommendation:', RankedProds)
    
        for pID, Rnk in RankedProds:
            Items = Items + str(pID) + "|"
            Ranks = Ranks + str(Rnk) + "|"

    return jsonify(ProductID = Items, Rank = Ranks)

def recommend_user_sim_products(AccountID, TopN):
    data = {'AccountId':AccountID, 'topN':TopN}
    resp = recommend_products()
	response = resp.get_json(force=True)
	Items = dict_lookup('ProductID', resp)
	Ranks = dict_lookup('Rank', resp)
    print(Items)
    print(Ranks)
    RankedProds = []
    ItemList = Items.split('|')[:TopN]
    RanksList = Ranks.split('|')[:TopN]
    print('Rank List:' ,RanksList)
    for i in range(len(ItemList)):
        RankedProds.append((ItemList[i], int(RanksList[i])))
    return RankedProds  