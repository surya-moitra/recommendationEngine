# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 21:41:37 2019

@author: sreens
"""
from flask import Flask, render_template,request, jsonify
import numpy as np
import pandas as pd
import pickle
import requests
import json
import UserBasedRecommendation as UserRec
import ProductBasedRecommendation as ProdRec
import Commonlybought_recommender as CommRec
import datetime
import operator
import re
import sys
sys.path.insert(0,"/var/www/FLASKAPPS/helloworldapp/")

with open('var/www/FLASKAPPS/helloworldapp/useritemdictUser.pickle', 'rb') as handle:
    userPurchaseItems = pickle.load(handle)
	
with open('var/www/FLASKAPPS/helloworldapp/clusterDF_prod.pickle', 'rb') as handle:
    ItemsDetailsDF = pickle.load(handle)
	
def dict_lookup(key, dictionary):
    if key in dictionary: 
        return dictionary[key]
    for value in dictionary.values():
        if isinstance(value, dict):
            dict_val = dict_lookup(key, value)
            if dict_val is not None: 
                return dict_val
    return None	

def sortedMerge(userSimRecs, prodSimRecs, commonlyBoughtRecs):
    
    listofTuples  = []
    prevprevRank  = -1
    prevprevIndex = -1
    prevRank      = -1
    prevIndex     = -1
    RecProddDF = pd.DataFrame()
    userSimRecs.sort(key = lambda x:x[1], reverse = True)
    prodSimRecs.sort(key = lambda x:x[1], reverse = True)
    commonlyBoughtRecs.sort(key = lambda x:x[1], reverse = True)
    while userSimRecs or prodSimRecs or commonlyBoughtRecs:
        listofTuples.clear()
        try:
            userRec = userSimRecs[0][1]
        except:
            userRec = -1
        try:
            prodRec = prodSimRecs[0][1]
        except:
            prodRec = -1
        try:
            apriRec = commonlyBoughtRecs[0][1]
        except:
            apriRec = -1
        listofTuples.append((0, userRec))
        listofTuples.append((1, prodRec))
        listofTuples.append((2, apriRec))
        listofTuples.sort(key = operator.itemgetter(1), reverse = True)
        
        candidate =  listofTuples[0]
        if candidate[1] == listofTuples[1][1] == listofTuples[2][1]:
            if (candidate[0] == prevIndex and candidate[1] == prevRank) or (candidate[0] == prevprevIndex and candidate[1] == prevprevRank):
                if listofTuples[1][0] != prevIndex and listofTuples[1][0] != prevprevIndex:
                    candidate = listofTuples[1]
                elif listofTuples[2][0] != prevIndex and listofTuples[2][0] != prevprevIndex:
                    candidate = listofTuples[2]
        elif candidate[1] == listofTuples[1][1]:
            if candidate[0] == prevIndex and candidate[1] == prevRank:
                candidate = listofTuples[1]

        prevprevRank  = prevRank
        prevprevIndex = prevIndex 
        prevRank = candidate[1]
        prevIndex = candidate[0]
        if prevIndex == 0:
            candidate = userSimRecs[0]
            userSimRecs.remove(candidate)
        elif prevIndex == 1:
            candidate = prodSimRecs[0]
            prodSimRecs.remove(candidate)
        elif prevIndex == 2:
            candidate = commonlyBoughtRecs[0]
            commonlyBoughtRecs.remove(candidate)
        RecProddDF = RecProddDF.append([candidate], ignore_index=True)

    RecProddDF.columns = ['ProductID', 'Rank']
    return RecProddDF
 
        
def ConsolidatedRecommendations():
    data = request.get_json(force=True)
    print('Consolidated User Similarity:',data)
    Weightages= None
    AccountID = dict_lookup('AccountId', data)
    ProductID = dict_lookup('ProductId', data)
    TopN = dict_lookup('topN', data)
    if not TopN:
        TopN = 10
    TopN = int(TopN)
    #AccountAttributes = dict_lookup('AccountAttributes', data)
    Weightages = dict_lookup('Weightage', data)
    if not Weightages:
        Weightages = 'W1:1,W2:1,W3:1'
    Items = ""
    Ranks = ""
    print('Input User Consolidated Recommendation:', AccountID, TopN)
    if AccountID:
        userSimRecs = UserRec.recommend_user_sim_products(AccountID, TopN)
        prodSimRecs = []
        commonlyBoughtRecs = []
        for prod in userPurchaseItems[AccountID]:
            prodSimRecs += ProdRec.get_individual_recommendation(prod, TopN)
            commonlyBoughtRecs += CommRec.get_individual_apriori_recommendation(prod, TopN)
        weight = re.findall(r":([\w.]+)", Weightages)
        try:
            W1 = float(weight[0])
            W2 = float(weight[1])
            W3 = float(weight[2])
        except:
            W1 = 1
            W2 = 1
            W3 = 1
			
        ConsolidatedDF = pd.DataFrame()
        userSimRecs = [[Prod, Rank*W1] for Prod, Rank in userSimRecs]
        userSimDF = pd.DataFrame(userSimRecs, columns = ['ProductID', 'Rank'])
        prodSimRecs = [[Prod, Rank*W2] for Prod, Rank in prodSimRecs]
        prodSimDF = pd.DataFrame(prodSimRecs, columns = ['ProductID', 'Rank'])
        commonlyBoughtRecs = [[Prod, Rank*W3] for Prod, Rank in commonlyBoughtRecs]
        AprioriDF = pd.DataFrame(commonlyBoughtRecs, columns = ['ProductID', 'Rank'])   
        userSimDF = userSimDF[userSimDF["ProductID"].isin(userPurchaseItems[AccountID]) == False]  
        prodSimDF = prodSimDF[prodSimDF["ProductID"].isin(userPurchaseItems[AccountID]) == False] 
        AprioriDF = AprioriDF[AprioriDF["ProductID"].isin(userPurchaseItems[AccountID]) == False]         
		
        if W1 != W2 != W3:    
            ConsolidatedDF = userSimDF.append(prodSimDF)
            ConsolidatedDF = ConsolidatedDF.append(AprioriDF)
            PriceDetails = []
			for ind, row in ConsolidatedDF.iterrows():
				CurrItemDF = ItemsDetailsDF[ItemsDetailsDF.Product_ID == row["ProductID"]]
				PriceDetails.append(float(CurrItemDF.Price.values[0]))
			ConsolidatedDF["Price"] = PriceDetails
			ConsolidatedDF = ConsolidatedDF.sort_values(by = ['Rank', 'Price'],  ascending=False)   
        else:
            ConsolidatedDF = sortedMerge(userSimRecs, prodSimRecs, commonlyBoughtRecs)
            ConsolidatedDF = ConsolidatedDF[ConsolidatedDF["ProductID"].isin(userPurchaseItems[AccountID]) == False]

        ConsolidatedDF = ConsolidatedDF.drop_duplicates(subset = ['ProductID'], keep = 'first')
        ConsolidatedDF = ConsolidatedDF[:TopN]
        RankedRecs = []
        for index, row in ConsolidatedDF.iterrows():
            RankedRecs.append((row['ProductID'], row['Rank']))
        print('Outpt User Consolidated Recommendation:', RankedRecs)
        for pID, Rnk in RankedRecs:
            Items = Items + str(pID) + "|"
            Ranks = Ranks + str(Rnk) + "|"
    
    return jsonify(ProductID = Items, Rank = Ranks)