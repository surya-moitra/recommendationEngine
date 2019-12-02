# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 13:34:10 2019

@author: sreens
"""
from flask import Flask, render_template,request, jsonify
import pandas as pd
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

with open('var/www/FLASKAPPS/helloworldapp/Ruleset_July24.pickle', 'rb') as handle:
    RulesDF = pickle.load( handle)

def get_individual_apriori_recommendation(pid, topN = 10):
    listofProducts = {}
    
    for index, row in RulesDF.iterrows():
        if pid in row.ProdID:
            for pds in row.ProdID:
                if pds != pid:
                    if pds in listofProducts:
                        if listofProducts[pds] < row['Lift']:
                            listofProducts[pds] = row['Lift']
                    else:
                        listofProducts[pds] = row['Lift']
    
    RankedProducts = sorted(listofProducts.items() , key=lambda x: x[1], reverse = True)

    Rank = topN
    priorLift = 0
    FirstProd = True
    RankedRecommendations = {}
    
    for prod, lift in RankedProducts:
        if FirstProd or lift == priorLift:
            if prod not in RankedRecommendations:
                RankedRecommendations[prod] = Rank
                FirstProd = False
                priorLift = lift
        else:
            if prod not in RankedRecommendations:
                Rank = Rank-1
                RankedRecommendations[prod] = Rank
                priorLift = lift
        if Rank < 1:
            break

    recommendations = [(prod,rank) for prod, rank in RankedRecommendations.items()]
    recommendations = recommendations[0:topN]
       
    #print(recommendations)
    return recommendations

def recommend_commonly_bought_prods():
    data = request.get_json(force=True)
    print('Apriori Request Data:',data)
    ProductID = dict_lookup('ProductId', data)
    TopN = dict_lookup('topN', data)
    if not TopN:
        TopN = 10
    TopN = int(TopN)
    Items = ""
    Ranks = ""
    if ProductID:
        print('Input of Apriori Recommendation:', ProductID, TopN)
        prods = re.findall(r"[\w-]+", ProductID)
        comBoughtRecs = []
        for prod in prods:
            comBoughtRecs += get_individual_apriori_recommendation(prod, TopN)
        ConsolidatedDF = pd.DataFrame(comBoughtRecs, columns = ['ProductID', 'Rank'])
        ConsolidatedDF = ConsolidatedDF.sort_values(by = ConsolidatedDF.columns[1],  ascending=False)
        ConsolidatedDF = ConsolidatedDF[ConsolidatedDF["ProductID"].isin(prods) == False]  
        ConsolidatedDF = ConsolidatedDF.drop_duplicates(subset = ['ProductID'], keep = 'first')
        ConsolidatedDF = ConsolidatedDF[:TopN]
        RankedRecs = []
        for index, row in ConsolidatedDF.iterrows():
            RankedRecs.append((row['ProductID'], row['Rank']))
        print('Outpt of Apriori Recommendation:', RankedRecs)
    
        for pID, Rnk in RankedRecs:
            Items = Items + str(pID) + "|"
            Ranks = Ranks + str(Rnk) + "|"
    
    return jsonify(ProductID = Items, Rank = Ranks)