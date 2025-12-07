import pandas as pd
import os
import numpy as np

CSV = os.environ.get('EV_CSV', '../../EV_Predictive_Maintenance_Dataset_15min.csv')
OUT_DIR = 'data/features'
os.makedirs(OUT_DIR, exist_ok=True)

def load_data(path=CSV):
    df = pd.read_csv(path, parse_dates=['Timestamp'])
    if 'VehicleID' not in df.columns:
        # create synthetic vehicle id if missing
        df['VehicleID'] = df.get('Vehicle', 'veh_unknown')
    df = df.sort_values(['VehicleID','Timestamp']).reset_index(drop=True)
    return df

def create_rolling_feats(df, windows=[3,6,12]):
    def _per_vehicle(g):
        g = g.set_index('Timestamp').sort_index()
        out = g.copy()
        numeric_cols = g.select_dtypes(include=['number']).columns.tolist()
        for c in numeric_cols:
            for w in windows:
                out[f"{c}_mean_{w}"] = g[c].rolling(window=w, min_periods=1).mean().fillna(0)
                out[f"{c}_std_{w}"] = g[c].rolling(window=w, min_periods=1).std().fillna(0)
        out = out.reset_index()
        return out
    feats = df.groupby('VehicleID', group_keys=False).apply(_per_vehicle).reset_index(drop=True)
    return feats

if __name__=='__main__':
    print('Loading data from', CSV)
    df = load_data()
    print('Original shape:', df.shape)
    feats = create_rolling_feats(df)
    out_path = os.path.join(OUT_DIR, 'features_all.parquet')
    feats.to_parquet(out_path, index=False)
    print('Saved features to', out_path)
