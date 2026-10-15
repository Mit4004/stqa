# Practical 9: Continuous Testing Pipeline using Jenkins

**Objective:** To implement a simple continuous testing pipeline using Jenkins for automated test execution.

---

## 📂 Files Included

- `calc.py` : Simple calculator module (functions: `add`, `subtract`, `multiply`, `divide`).
- `test_calc.py` : Automated test cases using `pytest`.
- `requirements.txt` : Lists test dependencies (`pytest`).
- `Jenkinsfile` : Declarative Jenkins pipeline script.

---

## 🛠️ Step-by-Step Jenkins Setup Guide

### Step 1: Open Jenkins Dashboard
1. Open your browser and navigate to `http://localhost:8080`.
2. Ensure the **JUnit Plugin** and **Pipeline Plugin** are installed in Jenkins (*Manage Jenkins -> Plugins*).

### Step 2: Create a New Pipeline Job
1. Click **New Item** on the Jenkins home page.
2. Enter item name: `stqa-continuous-testing`.
3. Select **Pipeline** and click **OK**.

### Step 3: Configure Git Repository
1. In the job configuration, scroll down to the **Pipeline** section.
2. Change **Definition** to: `Pipeline script from SCM`.
3. Select **SCM**: `Git`.
4. Set **Repository URL**: `https://github.com/Mit4004/stqa.git`.
5. Set **Branch Specifier**: `*/main`.
6. Set **Script Path**: `9/Jenkinsfile`.
7. Click **Save**.

### Step 4: Run the Pipeline
1. Click **Build Now** on the left menu.
2. Observe the pipeline stages execute:
   - `Checkout Code` -> Clones the GitHub repo.
   - `Install Dependencies` -> Installs `pytest`.
   - `Run Tests` -> Runs `pytest 9/test_calc.py` and outputs JUnit XML test report.
3. Check the **Test Result** tab to see the test trend and pass/fail summary!
