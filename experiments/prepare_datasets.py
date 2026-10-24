
import argparse, json, os, urllib.request
import pandas as pd
from sklearn import datasets as skd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ap = argparse.ArgumentParser()
ap.add_argument("--raw", default=os.path.join(HERE, "data", "raw"))
ap.add_argument("--out", default=os.path.join(HERE, "data", "clean"))
args = ap.parse_args()
RAW, OUT = args.raw, args.out
os.makedirs(RAW, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

GH = "https://raw.githubusercontent.com"
SOURCES = {
    "titanic.csv": f"{GH}/mwaskom/seaborn-data/master/titanic.csv",
    "penguins.csv": f"{GH}/mwaskom/seaborn-data/master/penguins.csv",
    "Telco-Customer-Churn.csv": f"{GH}/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv",
    "pima-indians-diabetes.data.csv": f"{GH}/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv",
    "banknote_authentication.csv": f"{GH}/jbrownlee/Datasets/master/banknote_authentication.csv",
    "ionosphere.csv": f"{GH}/jbrownlee/Datasets/master/ionosphere.csv",
    "sonar.csv": f"{GH}/jbrownlee/Datasets/master/sonar.csv",
    "glass.csv": f"{GH}/jbrownlee/Datasets/master/glass.csv",
    "wheat-seeds.csv": f"{GH}/jbrownlee/Datasets/master/wheat-seeds.csv",
    "adult-all.csv": f"{GH}/jbrownlee/Datasets/master/adult-all.csv",
    "haberman.csv": f"{GH}/jbrownlee/Datasets/master/haberman.csv",
    "ecoli.csv": f"{GH}/jbrownlee/Datasets/master/ecoli.csv",
    "Mall_Customers.csv": f"{GH}/SteffiPeTaffy/machineLearningAZ/master/Machine%20Learning%20A-Z%20Template%20Folder/Part%204%20-%20Clustering/Section%2024%20-%20K-Means%20Clustering/Mall_Customers.csv",
}
for name, url in SOURCES.items():
    path = os.path.join(RAW, name)
    if not os.path.exists(path):
        print("downloading", name)
        urllib.request.urlretrieve(url, path)
manifest = []

def save(name, df, target, source, task="classification", note=""):
    path = os.path.join(OUT, f"{name}.csv")
    df.to_csv(path, index=False)
    manifest.append({"name": name, "file": path, "target": target, "rows": len(df), "columns": df.shape[1],
                     "classes": int(df[target].nunique()) if target else None, "source": source, "task": task, "note": note})

for loader, name in [(skd.load_iris, "iris"), (skd.load_wine, "wine"), (skd.load_breast_cancer, "breast_cancer"), (skd.load_digits, "digits")]:
    b = loader(as_frame=True)
    df = b.frame.copy()
    df.columns = [str(c).replace(" (cm)", "").replace(" ", "_") for c in df.columns]
    df["target"] = [str(b.target_names[i]) if hasattr(b, "target_names") else str(i) for i in df["target"]]
    save(name, df.rename(columns={"target": "class"}), "class", "UCI via scikit-learn")

t = pd.read_csv(f"{RAW}/titanic.csv").drop(columns=["alive", "class", "who", "adult_male", "embark_town", "alone"])
t["survived"] = t["survived"].map({0: "no", 1: "yes"})
save("titanic", t, "survived", "Kaggle Titanic (seaborn-data mirror)", note="'alive' (label duplicate) and derived columns removed")

p = pd.read_csv(f"{RAW}/penguins.csv")
save("penguins", p, "species", "Palmer Penguins (seaborn-data mirror)")

tc = pd.read_csv(f"{RAW}/Telco-Customer-Churn.csv")
save("telco_churn", tc, "Churn", "IBM Telco Customer Churn", note="TotalCharges contains blank strings (mixed type)")

cols = ["pregnancies", "glucose", "blood_pressure", "skin_thickness", "insulin", "bmi", "pedigree", "age", "outcome"]
d = pd.read_csv(f"{RAW}/pima-indians-diabetes.data.csv", header=None, names=cols)
d["outcome"] = d["outcome"].map({0: "negative", 1: "positive"})
save("pima_diabetes", d, "outcome", "UCI Pima Indians Diabetes")

b = pd.read_csv(f"{RAW}/banknote_authentication.csv", header=None, names=["variance", "skewness", "curtosis", "entropy", "class"])
b["class"] = b["class"].map({0: "genuine", 1: "forged"})
save("banknote", b, "class", "UCI Banknote Authentication")

io = pd.read_csv(f"{RAW}/ionosphere.csv", header=None)
io.columns = [f"a{i}" for i in range(34)] + ["class"]
save("ionosphere", io, "class", "UCI Ionosphere")

so = pd.read_csv(f"{RAW}/sonar.csv", header=None)
so.columns = [f"band{i}" for i in range(60)] + ["class"]
save("sonar", so, "class", "UCI Sonar")

g = pd.read_csv(f"{RAW}/glass.csv", header=None, names=["RI", "Na", "Mg", "Al", "Si", "K", "Ca", "Ba", "Fe", "type"])
g["type"] = "type_" + g["type"].astype(str)
save("glass", g, "type", "UCI Glass Identification")

w = pd.read_csv(f"{RAW}/wheat-seeds.csv", header=None, names=["area", "perimeter", "compactness", "kernel_length", "kernel_width", "asymmetry", "groove_length", "variety"])
w["variety"] = w["variety"].map({1: "Kama", 2: "Rosa", 3: "Canadian"})
save("seeds", w, "variety", "UCI Seeds")

a = pd.read_csv(f"{RAW}/adult-all.csv", header=None, names=["age", "workclass", "fnlwgt", "education", "education_num", "marital_status", "occupation", "relationship", "race", "sex", "capital_gain", "capital_loss", "hours_per_week", "native_country", "income"], na_values="?")
save("adult", a, "income", "UCI Adult (Census Income)")

h = pd.read_csv(f"{RAW}/haberman.csv", header=None, names=["age", "operation_year", "positive_nodes", "survival"])
h["survival"] = h["survival"].map({1: "survived_5y", 2: "died_within_5y"})
save("haberman", h, "survival", "UCI Haberman's Survival")

e = pd.read_csv(f"{RAW}/ecoli.csv", header=None, names=["mcg", "gvh", "lip", "chg", "aac", "alm1", "alm2", "site"])
save("ecoli", e, "site", "UCI Ecoli", note="contains classes with 2 samples")

c = pd.read_excel(os.path.join(ROOT, "data", "customer_dataset.xlsx"))
save("guidml_customers", c, "Churn", "GuidML bundled synthetic customer dataset")

m = pd.read_csv(f"{RAW}/Mall_Customers.csv")
save("mall_customers", m, None, "Mall Customer Segmentation (Kaggle mirror)", task="clustering")

cc = pd.read_excel(os.path.join(ROOT, "data", "clustering_customer_dataset.xlsx"))
save("guidml_clustering", cc, None, "GuidML bundled clustering dataset", task="clustering")

json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=2)
for m_ in manifest: print(m_["name"], m_["rows"], m_["columns"], m_["classes"])
