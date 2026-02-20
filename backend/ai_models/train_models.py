"""
SDARS Machine Learning Model Training Pipeline
Trains RandomForest classifiers for Fire, Flood, and Cyclone prediction
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib
import os
import sys
import json
from datetime import datetime

# Add parent to path for config access
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from ai_models.training_data_generator import generate_training_data, save_training_data


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   🧠 SDARS AI MODEL TRAINING PIPELINE                                ║
║   Training Real Machine Learning Models for Disaster Prediction      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)


def load_or_generate_data():
    """Load existing training data or generate new synthetic data"""
    training_dir = os.path.join(config.DATA_DIR, 'training')
    data_path = os.path.join(training_dir, 'disaster_data.csv')
    
    if os.path.exists(data_path):
        print(f"📂 Loading existing training data from: {data_path}")
        df = pd.read_csv(data_path)
        print(f"   ✓ Loaded {len(df)} samples")
    else:
        print("📂 No existing data found. Generating new synthetic dataset...")
        df = generate_training_data(n_samples=10000)
        save_training_data(df)
    
    return df


def train_disaster_model(X_train, X_test, y_train, y_test, disaster_type: str):
    """
    Train a single disaster prediction model
    Uses RandomForest with optimized hyperparameters
    """
    print(f"\n{'='*60}")
    print(f"🎯 TRAINING: {disaster_type.upper()} RISK MODEL")
    print('='*60)
    
    # Model configuration
    model = RandomForestClassifier(
        n_estimators=150,      # Number of trees
        max_depth=12,          # Prevent overfitting
        min_samples_split=5,   # Minimum samples to split
        min_samples_leaf=2,    # Minimum samples in leaf
        class_weight='balanced',  # Handle class imbalance
        random_state=42,
        n_jobs=-1              # Use all cores
    )
    
    # Train the model
    print("   🔄 Training model...")
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    # Cross-validation score
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1')
    
    print(f"\n   📊 MODEL PERFORMANCE:")
    print(f"   ├── Accuracy:  {accuracy:.2%}")
    print(f"   ├── Precision: {precision:.2%}")
    print(f"   ├── Recall:    {recall:.2%}")
    print(f"   ├── F1 Score:  {f1:.2%}")
    print(f"   └── CV F1:     {cv_scores.mean():.2%} (±{cv_scores.std():.2%})")
    
    # Feature importance
    feature_names = ['temp', 'hum', 'wind', 'press', 'ndvi', 'ndwi', 'hotspots']
    importance = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n   🔍 FEATURE IMPORTANCE:")
    for _, row in importance.iterrows():
        bar = '█' * int(row['importance'] * 40)
        print(f"   {row['feature']:10} {bar} {row['importance']:.3f}")
    
    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    print(f"\n   📋 CONFUSION MATRIX:")
    print(f"   ┌─────────────┬─────────────┐")
    print(f"   │ TN: {cm[0][0]:5}  │ FP: {cm[0][1]:5}  │")
    print(f"   ├─────────────┼─────────────┤")
    print(f"   │ FN: {cm[1][0]:5}  │ TP: {cm[1][1]:5}  │")
    print(f"   └─────────────┴─────────────┘")
    
    return model, {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'cv_f1_mean': cv_scores.mean(),
        'cv_f1_std': cv_scores.std(),
        'feature_importance': importance.to_dict('records')
    }


def save_model(model, disaster_type: str, metrics: dict):
    """Save the trained model and its metrics"""
    # Ensure models directory exists
    os.makedirs(config.MODELS_DIR, exist_ok=True)
    
    # Save model
    model_filename = f"{disaster_type}_risk_model.joblib"
    model_path = os.path.join(config.MODELS_DIR, model_filename)
    joblib.dump(model, model_path)
    print(f"\n   💾 Model saved: {model_path}")
    
    # Save metrics
    metrics_filename = f"{disaster_type}_model_metrics.json"
    metrics_path = os.path.join(config.MODELS_DIR, metrics_filename)
    metrics['trained_at'] = datetime.now().isoformat()
    metrics['model_path'] = model_path
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"   📊 Metrics saved: {metrics_path}")
    
    return model_path


def train_all_models():
    """Main training pipeline - trains all disaster prediction models"""
    print_banner()
    
    # Step 1: Load or generate data
    print("\n📊 STEP 1: DATA PREPARATION")
    print("-" * 40)
    df = load_or_generate_data()
    
    # Step 2: Prepare features and targets
    print("\n🔧 STEP 2: FEATURE ENGINEERING")
    print("-" * 40)
    
    feature_columns = ['temp', 'hum', 'wind', 'press', 'ndvi', 'ndwi', 'hotspots']
    target_columns = ['fire_risk', 'flood_risk', 'cyclone_risk']
    
    X = df[feature_columns]
    print(f"   ✓ Features: {feature_columns}")
    print(f"   ✓ Feature matrix shape: {X.shape}")
    
    # Step 3: Train-test split (same split for all models for fair comparison)
    X_train, X_test, indices_train, indices_test = train_test_split(
        X, df.index, test_size=0.2, random_state=42
    )
    
    print(f"   ✓ Training samples: {len(X_train)}")
    print(f"   ✓ Test samples: {len(X_test)}")
    
    # Step 4: Train each model
    print("\n🧠 STEP 3: MODEL TRAINING")
    print("-" * 40)
    
    trained_models = {}
    all_metrics = {}
    
    for disaster_type in ['fire', 'flood', 'cyclone']:
        target = f"{disaster_type}_risk"
        y_train = df.loc[indices_train, target]
        y_test = df.loc[indices_test, target]
        
        model, metrics = train_disaster_model(
            X_train, X_test, y_train, y_test, disaster_type
        )
        
        save_model(model, disaster_type, metrics)
        trained_models[disaster_type] = model
        all_metrics[disaster_type] = metrics
    
    # Step 5: Summary
    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE - MODEL SUMMARY")
    print("=" * 60)
    
    print("\n📈 FINAL MODEL PERFORMANCE:")
    print("-" * 50)
    print(f"{'Model':<12} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-" * 50)
    
    for disaster_type, metrics in all_metrics.items():
        print(f"{disaster_type.upper():<12} {metrics['accuracy']:>10.2%} {metrics['precision']:>10.2%} {metrics['recall']:>10.2%} {metrics['f1']:>10.2%}")
    
    print("-" * 50)
    
    # Calculate overall performance
    avg_f1 = np.mean([m['f1'] for m in all_metrics.values()])
    print(f"\n🏆 OVERALL AVERAGE F1 SCORE: {avg_f1:.2%}")
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ✅ ALL MODELS TRAINED AND SAVED!                                   ║
║                                                                      ║
║   Models location: {config.MODELS_DIR:<43}║
║                                                                      ║
║   Files created:                                                     ║
║   • fire_risk_model.joblib                                           ║
║   • flood_risk_model.joblib                                          ║
║   • cyclone_risk_model.joblib                                        ║
║                                                                      ║
║   🚀 Your AI is now REAL machine learning!                           ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    return trained_models, all_metrics


if __name__ == "__main__":
    train_all_models()
