# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 21:41:37 2019

@author: sreens
"""
from flask import Flask, render_template,request, jsonify
import numpy as np
import pandas as pd
import requests
import json
import ProductBasedRecommendation as ProdRec
import Commonlybought_recommender as CommRec
from flask import jsonify
import operator
import re
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

def sortedMerge(prodSimRecs, commonlyBoughtRecs):
    
    listofTuples = []
    prevRank     = -1
    prevIndex    = -1
    RecProddDF = pd.DataFrame()
    prodSimRecs.sort(key = lambda x:x[1], reverse = True)
    commonlyBoughtRecs.sort(key = lambda x:x[1], reverse = True)
    while prodSimRecs or commonlyBoughtRecs:
        listofTuples.clear()
        try:
            prodRec = prodSimRecs[0][1]
        except:
            prodRec = -1
        try:
            apriRec = commonlyBoughtRecs[0][1]
        except:
            apriRec = -1
        listofTuples.append((0, prodRec))
        listofTuples.append((1, apriRec))
        listofTuples.sort(key = operator.itemgetter(1), reverse = True)
        
        candidate =  listofTuples[0]
        if candidate[0] == prevIndex and candidate[1] == prevRank:
            if listofTuples[1][1] == candidate[1]:
                candidate = listofTuples[1]
        prevRank = candidate[1]
        prevIndex = candidate[0]
        if prevIndex == 0:
            candidate = prodSimRecs[0]
        elif prevIndex == 1:
            candidate = commonlyBoughtRecs[0]
        RecProddDF = RecProddDF.append([candidate], ignore_index=True)
        if prevIndex == 0:
            prodSimRecs.remove(candidate)
        elif prevIndex == 1:
            commonlyBoughtRecs.remove(candidate)
    RecProddDF.columns = ['ProductID', 'Rank']
    return RecProddDF

def ConsolidatedRecommendations():
    data = request.get_json(force=True)
    print('Consolidated Product Similarity Request Data:',data)
    Weightages= None
    ProductID = dict_lookup('ProductId', data)
    TopN = dict_lookup('topN', data)
    if not TopN:
        TopN = 10
    TopN = int(TopN)
    #ProductAttributes = dict_lookup('ProductAttributes', data)
    Weightages = dict_lookup('Weightage', data)
    if not Weightages:
        Weightages= 'W1:1,W2:1'
    Items = ""
    Ranks = ""
    print('Input Product and TopN for Consolidated Product Recommendation:', ProductID, TopN)
    if ProductID:
        prodSimRecs = ProdRec.get_individual_recommendation(ProductID, TopN)
        commonlyBoughtRecs = CommRec.get_individual_apriori_recommendation(ProductID, TopN)
		
        weight = re.findall(r":([\w.]+)", Weightages)
        try:
            W1 = float(weight[0])
            W2 = float(weight[1])
        except:
            W1 = 1
            W2 = 1       

        prodSimRecs = [[Prod, Rank*W1] for Prod, Rank in prodSimRecs]
        prodSimDF = pd.DataFrame(prodSimRecs, columns = ['ProductID', 'Rank'])
        commonlyBoughtRecs = [[Prod, Rank*W2] for Prod, Rank in commonlyBoughtRecs]
        AprioriDF = pd.DataFrame(commonlyBoughtRecs, columns = ['ProductID', 'Rank'])   
        ConsolidatedDF = pd.DataFrame()
		
        if W1 != W2:
            ConsolidatedDF = prodSimDF.append(AprioriDF)
            ConsolidatedDF = ConsolidatedDF.sort_values(by = ConsolidatedDF.columns[1],  ascending=False)

        else:
            ConsolidatedDF = sortedMerge(prodSimRecs, commonlyBoughtRecs)

        ConsolidatedDF = ConsolidatedDF.drop_duplicates(subset = ['ProductID'], keep = 'first')
        ConsolidatedDF = ConsolidatedDF[:TopN]                
        RankedRecs = []
        for index, row in ConsolidatedDF.iterrows():
            RankedRecs.append((row['ProductID'], row['Rank']))
        print('Output Products for  Consolidated Product Recommendation:', RankedRecs)
    
        for pID, Rnk in RankedRecs:
            Items = Items + str(pID) + "|"
            Ranks = Ranks + str(Rnk) + "|"
    
    return jsonify(ProductID = Items, Rank = Ranks)  