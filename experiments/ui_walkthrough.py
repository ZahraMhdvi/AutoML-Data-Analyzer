import os, sys, time, json
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "clean")
errors = []
os.makedirs(SHOTS, exist_ok=True)

def wait_idle(page):
    page.wait_for_function("() => !document.getElementById('loadingOverlay').classList.contains('loading-overlay--visible')", timeout=600000)
    time.sleep(0.8)

def shot(page, name, full=True):
    page.evaluate("window.scrollTo(0, 0); document.getElementById('toastContainer').innerHTML = ''"); time.sleep(0.3)
    page.screenshot(path=f"{SHOTS}/{name}.png", full_page=full)
    print("shot", name)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1366, "height": 900}, device_scale_factor=2)
    page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

    page.goto(BASE + "/#/signup"); time.sleep(1.2)
    shot(page, "00_auth_en", full=False)
    page.fill("#signupName", "Zahra"); page.fill("#signupEmail", "demo@guidml.test"); page.fill("#signupPassword", "secret123")
    page.click("#signupForm button[type=submit]"); time.sleep(1.5)

    # --- classification project: Telco churn
    page.goto(BASE + "/#/new"); time.sleep(0.6)
    page.set_input_files("#datasetFile", f"{DATA}/telco_churn.csv")
    page.fill("#projectName", "Telco Customer Churn")
    page.click("#analyzeBtn"); wait_idle(page); time.sleep(1)
    shot(page, "01_problem_en")
    page.click("[data-problem=classification]"); time.sleep(0.8)
    shot(page, "02_target_en")
    page.click("[data-target=Churn]"); wait_idle(page)
    page.check("input[name=goal][value=accuracy]"); page.check("input[name=growth][value=static_data]"); time.sleep(1.2)
    shot(page, "03_prefs_en")
    page.click("#submitPreferencesBtn"); wait_idle(page)
    shot(page, "04_models_en")
    page.click("[data-algorithm]"); wait_idle(page); time.sleep(2)
    shot(page, "05_dashboard_en")


    page.click("[data-locale-option='fa-IR']"); wait_idle(page); time.sleep(2)
    shot(page, "06_dashboard_fa")
    page.click("[data-locale-option='en-US']"); wait_idle(page); time.sleep(1)


    page.goto(BASE + "/#/new"); time.sleep(0.6)
    page.set_input_files("#datasetFile", f"{DATA}/mall_customers.csv")
    page.fill("#projectName", "Mall Customer Segmentation")
    page.click("#analyzeBtn"); wait_idle(page); time.sleep(1)
    page.click("[data-problem=clustering]"); time.sleep(0.6)
    page.check("input[name=cluster_goal][value=customer_segmentation]"); page.check("input[name=cluster_number][value=unknown]")
    time.sleep(0.8)
    page.click("#submitClusteringBtn"); wait_idle(page)
    shot(page, "07_cluster_models_en")
    page.click("[data-algorithm='KMeans']"); wait_idle(page); time.sleep(2)
    shot(page, "08_cluster_dashboard_en")


    page.goto(BASE + "/#/new"); time.sleep(0.6)
    page.set_input_files("#datasetFile", f"{DATA}/guidml_clustering.csv")
    page.fill("#projectName", "Customer Value (pseudo-target)")
    page.click("#analyzeBtn"); wait_idle(page); time.sleep(1)
    page.click("[data-problem=classification]"); time.sleep(0.6)
    shot(page, "09_target_options_en")
    page.click("#aiTargetBtn"); wait_idle(page); time.sleep(0.8)
    page.click("details.disclosure >> nth=0"); page.click("details.disclosure >> nth=1"); time.sleep(0.5)
    shot(page, "10_pseudo_target_en")
    page.click("#acceptAiBtn"); time.sleep(0.6)
    page.check("input[name=goal][value=interpretability]"); page.check("input[name=growth][value=continuous_data]"); time.sleep(1)
    page.click("#submitPreferencesBtn"); wait_idle(page)
    page.click("[data-algorithm='Decision Tree']"); wait_idle(page); time.sleep(2)
    shot(page, "11_pseudo_dashboard_en")

    page.goto(BASE + "/#/projects"); time.sleep(1.5)
    shot(page, "12_projects_en")
    page.click("[data-locale-option='fa-IR']"); time.sleep(1.5)
    shot(page, "13_projects_fa")
    page.click("[data-locale-option='en-US']"); time.sleep(1)
    browser.close()

print("CONSOLE:", json.dumps(errors, indent=1))
