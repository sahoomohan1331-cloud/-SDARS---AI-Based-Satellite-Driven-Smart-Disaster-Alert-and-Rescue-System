"""
SDARS Machine Learning Model Training Pipeline
Trains High-Accuracy RandomForest classifiers for ALL 8 Hazard Types:
  1. Cyclone
  2. Flood
  3. Drought
  4. Heatwave
  5. Lightning
  6. Landslide
  7. Storm Surge
  8. Wildfire
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
import os
import sys
import json
from datetime import datetime

# Add parent to path for config access
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure Windows UTF-8 stdout
try:
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import config
from ai_models.training_data_generator import generate_training_data, save_training_data, FEATURE_COLUMNS, TARGET_COLUMNS


DISASTER_MAP = {
    'cyclone': 'cyclone_risk',
    'flood': 'flood_risk',
    'drought': 'drought_risk',
    'heatwave': 'heatwave_risk',
    'lightning': 'lightning_risk',
    'landslide': 'landslide_risk',
    'storm_surge': 'storm_surge_risk',
    'fire': 'fire_risk'
}

def load_or_generate_data():
    """Load existing training data or generate new synthetic data"""
    training_dir = os.path.join(config.DATA_DIR, 'training')
    data_path = os.path.join(training_dir, 'disaster_data.csv')
    
    # Check if existing data contains all 13 features and 8 targets
    needs_gen = True
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        if all(c in df.columns for c in FEATURE_COLUMNS) and all(c in df.columns for c in TARGET_COLUMNS):
            print(f"📂 Loading existing comprehensive training data from: {data_path} ({len(df)} samples)")
            needs_gen = False
            return df
            
    print("📂 Generating new 16,000-sample high-precision multi-hazard dataset...")
    df = generate_training_data(n_samples=16000)
    save_training_data(df)
    return df

def train_disaster_model(X_train, X_test, y_train, y_test, disaster_type: str):
    """
    Train a single disaster prediction model with RandomForest
    """
    print(f"\n{'='*60}")
    print(f"🎯 TRAINING: {disaster_type.upper()} RISK MODEL")
    print('='*60)
    
    model = RandomForestClassifier(
        n_estimators=160,
        max_depth=14,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1')
    
    print(f"   📊 MODEL PERFORMANCE:")
    print(f"   ├── Accuracy:  {accuracy:.2%}")
    print(f"   ├── Precision: {precision:.2%}")
    print(f"   ├── Recall:    {recall:.2%}")
    print(f"   ├── F1 Score:  {f1:.2%}")
    print(f"   └── CV F1:     {cv_scores.mean():.2%} (±{cv_scores.std():.2%})")
    
    importance = pd.DataFrame({
        'feature': FEATURE_COLUMNS,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"   🔍 TOP 3 KEY FEATURES:")
    for _, row in importance.head(3).iterrows():
        print(f"       • {row['feature']:18} {row['importance']:.3f}")
    
    cm = confusion_matrix(y_test, y_pred)
    
    return model, {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'cv_f1_mean': float(cv_scores.mean()),
        'cv_f1_std': float(cv_scores.std()),
        'confusion_matrix': cm.tolist(),
        'feature_importance': importance.to_dict('records')
    }

def save_model(model, disaster_type: str, metrics: dict):
    os.makedirs(config.MODELS_DIR, exist_ok=True)
    
    model_filename = f"{disaster_type}_risk_model.joblib"
    model_path = os.path.join(config.MODELS_DIR, model_filename)
    joblib.dump(model, model_path)
    
    metrics_filename = f"{disaster_type}_model_metrics.json"
    metrics_path = os.path.join(config.MODELS_DIR, metrics_filename)
    metrics['disaster_type'] = disaster_type
    metrics['features'] = FEATURE_COLUMNS
    metrics['trained_at'] = datetime.now().isoformat()
    metrics['model_path'] = model_path
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    print(f"   💾 Saved model and metrics to: {model_path}")
    return model_path

def train_all_models():
    """Trains tuned ML models across ALL 8 hazards"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   🧠 SDARS AI MODEL TRAINING PIPELINE - 8 HAZARD ACCURACY UPGRADE    ║
║   Training Calibrated RandomForest Classifiers on Physics Telemetry  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    df = load_or_generate_data()
    
    X = df[FEATURE_COLUMNS]
    X_train, X_test, indices_train, indices_test = train_test_split(
        X, df.index, test_size=0.2, random_state=42
    )
    
    print(f"\n🔧 Feature Matrix: {X.shape[1]} inputs across {len(X_train)} train / {len(X_test)} test instances.")
    
    trained_models = {}
    all_metrics = {}
    
    for disaster_type, target_col in DISASTER_MAP.items():
        y_train = df.loc[indices_train, target_col]
        y_test = df.loc[indices_test, target_col]
        
        model, metrics = train_disaster_model(
            X_train, X_test, y_train, y_test, disaster_type
        )
        save_model(model, disaster_type, metrics)
        trained_models[disaster_type] = model
        all_metrics[disaster_type] = metrics
        
    print("\n" + "=" * 70)
    print("🏆 FINAL MULTI-HAZARD MODEL PERFORMANCE EVALUATION")
    print("=" * 70)
    print(f"{'Hazard Model':<16} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1 Score':>10}")
    print("-" * 70)
    for dt, m in all_metrics.items():
        print(f"{dt.upper():<16} {m['accuracy']:>10.2%} {m['precision']:>10.2%} {m['recall']:>10.2%} {m['f1']:>10.2%}")
    print("-" * 70)
    
    avg_acc = np.mean([m['accuracy'] for m in all_metrics.values()])
    avg_f1 = np.mean([m['f1'] for m in all_metrics.values()])
    print(f"\n🌟 SYSTEM-WIDE MEAN ACCURACY: {avg_acc:.2%}")
    print(f"🌟 SYSTEM-WIDE MEAN F1 SCORE: {avg_f1:.2%}")
    
    return trained_models, all_metrics

if __name__ == "__main__":
    train_all_models()
