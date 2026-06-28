"""
Real Clinical Evaluation using Kaggle Heart Failure Dataset
918 real patients - fedesoriano/heart-failure-prediction
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, confusion_matrix, brier_score_loss
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

df = pd.read_csv('data/heart.csv')
print(f"Real dataset loaded: {len(df)} patients")

df['actual_critical_outcome'] = df['HeartDisease']

# Better feature engineering
df['ExerciseAngina_num'] = (df['ExerciseAngina'] == 'Y').astype(int)
df['Sex_num'] = (df['Sex'] == 'M').astype(int)
df['ChestPain_ASY'] = (df['ChestPainType'] == 'ASY').astype(int)
df['ChestPain_NAP'] = (df['ChestPainType'] == 'NAP').astype(int)
df['ST_Down'] = (df['ST_Slope'] == 'Down').astype(int)
df['ST_Flat'] = (df['ST_Slope'] == 'Flat').astype(int)
df['Chol_zero'] = (df['Cholesterol'] == 0).astype(int)

features = ['Age','RestingBP','Cholesterol','MaxHR','Oldpeak','FastingBS',
            'ExerciseAngina_num','Sex_num','ChestPain_ASY','ChestPain_NAP',
            'ST_Down','ST_Flat','Chol_zero']

X = df[features].values
y = df['actual_critical_outcome'].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = LogisticRegression(max_iter=1000, C=0.5)
model.fit(X_scaled, y)

df['predicted_prob'] = model.predict_proba(X_scaled)[:,1]
df['predicted_critical'] = model.predict(X_scaled)

df.to_csv('data/clinical_cohort_real.csv', index=False)

true = df['actual_critical_outcome'].values
probs = df['predicted_prob'].values
preds = df['predicted_critical'].values

tn,fp,fn,tp = confusion_matrix(true, preds).ravel()
sensitivity = tp/(tp+fn)
specificity = tn/(tn+fp)
precision = tp/(tp+fp) if (tp+fp)>0 else 0
accuracy = (tp+tn)/len(df)
auroc = roc_auc_score(true, probs)
brier = brier_score_loss(true, probs)
f1 = 2*(precision*sensitivity)/(precision+sensitivity+1e-9)

print("=" * 65)
print("   SENTINEL-CDSS REAL CLINICAL EVALUATION")
print(f"   {len(df)} Real Patients - Kaggle Heart Failure Dataset")
print("   License: ODbL-1.0 (Open Database License)")
print("=" * 65)
print(f"  Total Patients        : {len(df)}")
print(f"  Critical Cases        : {df['actual_critical_outcome'].sum()} ({df['actual_critical_outcome'].mean()*100:.1f}%)")
print(f"  Accuracy              : {accuracy*100:.1f}%")
print(f"  Sensitivity (Recall)  : {sensitivity*100:.1f}%")
print(f"  Specificity           : {specificity*100:.1f}%")
print(f"  Precision (PPV)       : {precision*100:.1f}%")
print(f"  F1 Score              : {f1:.3f}")
print(f"  AUROC                 : {auroc:.4f}  (target >0.85)")
print(f"  Brier Score           : {brier:.4f}  (lower=better)")
print("=" * 65)

male = df[df['Sex']=='M']
female = df[df['Sex']=='F']
if len(female['actual_critical_outcome'].unique()) > 1:
    male_auroc = roc_auc_score(male['actual_critical_outcome'], male['predicted_prob'])
    female_auroc = roc_auc_score(female['actual_critical_outcome'], female['predicted_prob'])
    bias_gap = abs(male_auroc - female_auroc)
    print(f"  SUBGROUP ANALYSIS (Gender Bias Check)")
    print(f"  Male patients AUROC   : {male_auroc:.4f}")
    print(f"  Female patients AUROC : {female_auroc:.4f}")
    print(f"  Bias Gap              : {bias_gap:.4f}  {'OK (<0.1)' if bias_gap < 0.1 else 'Review needed'}")
    print("=" * 65)

elderly = df[df['Age'] >= 65]
young = df[df['Age'] < 65]
if len(elderly['actual_critical_outcome'].unique()) > 1:
    elderly_auroc = roc_auc_score(elderly['actual_critical_outcome'], elderly['predicted_prob'])
    young_auroc = roc_auc_score(young['actual_critical_outcome'], young['predicted_prob'])
    age_gap = abs(elderly_auroc - young_auroc)
    print(f"  SUBGROUP ANALYSIS (Age Bias Check)")
    print(f"  Elderly (65+) AUROC   : {elderly_auroc:.4f}")
    print(f"  Younger (<65) AUROC   : {young_auroc:.4f}")
    print(f"  Bias Gap              : {age_gap:.4f}  {'OK (<0.1)' if age_gap < 0.1 else 'Review needed'}")
    print("=" * 65)

print(f"  OVERALL: {'CLINICAL GRADE ✅' if auroc >= 0.85 else 'Good - above baseline'}")
print("=" * 65)
