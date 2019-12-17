from flask import Flask,render_template,request, jsonify
import pandas as pd
import json
import string
import ProductBasedRecommendation as ProdRecommender
import UserBasedRecommendation as UserRecommender
import Commonlybought_recommender as AprioryRec
import ConsolidatedProductRecommendation as ConsProdRec
import ConsolidatedUserRecommendation as ConsUserRec

def ProductClusterRecommendation(productId):
    data = (productId)
    Items,Ranks = ProdRecommender.recommend_similar_products(data)
    return Items,Ranks

def UserClusterRecommendation(userId):
    data = (userId)
    Items,Ranks = UserRecommender.recommend_products(data)
    return Items,Ranks

def CommonlyboughtRecommendation(productId):
    data = (productId)
    Items,Ranks = AprioryRec.recommend_commonly_bought_prods(data)
    return Items,Ranks

def ConsolidatedProductRecommendations(productId):
    data = (productId)
    Items,Ranks = ConsProdRec.ConsolidatedRecommendations(data)
    return Items,Ranks

def ConsolidatedUserRecommendations(userId):
    data = (userId)
    Items,Ranks = ConsUserRec.ConsolidatedRecommendations(data)
    return Items,Ranks

# some bits of text for the page.
header_text = '''
    <html>\n<head> <title>Generic Recommendation Engine</title> </head>\n<body>'''
instructions = '''
    <p><em>Hint</em>: This is a RESTful web service! Append a Product Id to the URL (for example: <code>/32432156</code>) to get Product Recommendations.</p>\n'''
home_link = '<p><a href="/">Back</a></p>\n'
footer_text = '</body>\n</html>'

# EB looks for an 'application' callable by default.
application = Flask(__name__)

# add a rule for the index page.
application.add_url_rule('/', 'index', (lambda: header_text + instructions + footer_text))

# add a rule when the page is accessed with a name appended to the site URL

#Product Reco eg: http://127.0.0.1:5000/model/ProductSimilarity/88-1WBKFK
application.add_url_rule('/model/ProductSimilarity/<productId>', 'product recommendations  ', (lambda productId:
    ProductClusterRecommendation(productId) ))

#User Reco eg: http://127.0.0.1:5000/model/UserSimilarity/88-1W96LL
application.add_url_rule('/model/UserSimilarity/<userId>', 'user recommendations  ', (lambda userId:
    UserClusterRecommendation(userId) ))

#Commonly bought Reco eg: http://127.0.0.1:5000/model/CommonlyBoughtTogether/88-1WBKFK
application.add_url_rule('/model/CommonlyBoughtTogether/<productId>', 'commonly bought recommendations  ', (lambda productId:
    CommonlyboughtRecommendation(productId) ))

#Consolidated Product Reco eg: http://127.0.0.1:5000/model/ProductBasedRecommendation/88-1WBKFK
application.add_url_rule('/model/ProductBasedRecommendation/<productId>', 'consolidated Product Reco  ', (lambda productId:
    ConsolidatedProductRecommendations(productId) ))

#Consolidated User Reco eg: http://127.0.0.1:5000/model/UserBasedRecommendation/88-1W96LL
# AWS deployed URI: http://flask-env.kjadmuuj8p.us-east-2.elasticbeanstalk.com/model/UserBasedRecommendation/88-1W96LL
application.add_url_rule('/model/UserBasedRecommendation/<userId>', 'consolidated User Reco  ', (lambda userId:
    ConsolidatedUserRecommendations(userId) ))

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()