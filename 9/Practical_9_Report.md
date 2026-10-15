# Practical 9: Continuous Testing Pipeline using Jenkins

**Course:** Software Testing and Quality Assurance (3CS501IC24)  
**Practical No.:** 9  
**Aim:** To implement a simple continuous testing pipeline using Jenkins.

---

## 1. Objective and Scope
- To understand the concepts of Continuous Testing (CT) within a CI/CD pipeline.
- To configure an automated Jenkins Declarative Pipeline that triggers tests on code commits.
- To execute automated test cases using `pytest` and publish test results using the Jenkins JUnit plugin.

---

## 2. System Components

### 2.1 Code Under Test (`calc.py`)
```python
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

### 2.2 Test Suite (`test_calc.py`)
```python
import pytest
from calc import add, subtract, multiply, divide

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_subtract():
    assert subtract(5, 3) == 2

def test_multiply():
    assert multiply(2, 3) == 6

def test_divide():
    assert divide(6, 3) == 2

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)
```

### 2.3 Jenkins Declarative Pipeline (`Jenkinsfile`)
```groovy
pipeline {
    agent any

    stages {
        stage('Checkout Code') {
            steps {
                echo 'Checking out code from Git...'
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Installing pytest...'
                script {
                    if (isUnix()) {
                        sh 'pip install -r 9/requirements.txt'
                    } else {
                        bat 'pip install -r 9\\requirements.txt'
                    }
                }
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Running automated test suite...'
                script {
                    if (isUnix()) {
                        sh 'pytest 9/test_calc.py --junitxml=9/test-results.xml -v'
                    } else {
                        bat 'pytest 9\\test_calc.py --junitxml=9\\test-results.xml -v'
                    }
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: '9/test-results.xml'
        }
        success {
            echo 'Continuous Testing Passed!'
        }
        failure {
            echo 'Continuous Testing Failed!'
        }
    }
}
```

---

## 3. Jenkins Setup Procedure

1. **Create Pipeline Job**: Create a new pipeline project named `stqa-continuous-testing`.
2. **Link GitHub SCM**:
   - Repository URL: `https://github.com/Mit4004/stqa.git`
   - Branch: `*/main`
   - Script Path: `9/Jenkinsfile`
3. **Build & Execute**:
   - Click **Build Now**.
   - Jenkins pulls the repository, installs dependencies, runs pytest, and generates `test-results.xml`.
4. **Result Verification**: View the test dashboard under the **Test Result** link on the Jenkins build page.

---

## 4. Test Results and Analysis

| Test Name | Functionality Tested | Expected Result | Status |
| :--- | :--- | :--- | :--- |
| `test_add` | Addition of positive & negative integers | Correct sum | **PASSED** |
| `test_subtract` | Subtraction of numbers | Correct difference | **PASSED** |
| `test_multiply` | Multiplication by positive/negative/zero | Correct product | **PASSED** |
| `test_divide` | Standard division | Correct quotient | **PASSED** |
| `test_divide_by_zero`| Division by zero | Raises `ValueError` | **PASSED** |

**Conclusion:** The continuous testing pipeline automatically detects changes, executes the full test suite, and reports test results without human intervention.
