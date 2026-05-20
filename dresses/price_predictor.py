import joblib
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

bundle = joblib.load(MODEL_PATH)

model = bundle['model']
le_category = bundle['le_category']
le_season = bundle['le_season']


def predict_price(product_views, sales, base_price, category, season, vehicle_type):

    category_enc = le_category.transform([category])[0]
    season_enc = le_season.transform([season])[0]

    X = pd.DataFrame([{
        'product_views': product_views,
        'sales': sales,
        'base_price': base_price,
        'category_enc': category_enc,
        'season_enc': season_enc
    }])

    prediction = model.predict(X)[0]

    return round(prediction, 2)