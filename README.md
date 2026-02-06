# SafeShieldCV (SSCV) 🛡️👷‍♂️
Real-time AI-Powered PPE Detection & Reporting System

### 🏢 Developed by Team-TASK (Tchana, Aloknath, Subhadra, Krishna)
Providing AI-automated digital solutions. We offer a full pipeline: Consultation, Implementation, Deployment, and Services.

### 📝 Project Overview
SafeShieldCV is a proactive industrial safety solution designed to automate PPE (Personal Protective Equipment) monitoring. Utilizing Computer Vision and Large Language Models (LLMs), the system identifies safety violations in real-time, documents evidence, and automates the reporting workflow for supervisors.

In high-risk environments, human oversight is often inconsistent. SafeShieldCV provides 24/7 vigilance, ensuring that helmet, vest, and glove violations are caught and reported instantly to maintain a zero-incident culture.

📂 Project Structure

```
├── 📁 backend
│   └── 🐍 main.py
├── 📁 configs
│   └── ⚙️ backend_config.env
│   └── 📄 frontend_config.json
├── 📁 frontend
│   └── 📁 sscv-desktop-app
│       └── 🐍 app.py
├── 📁 models
├── 📁 notebooks
├── ⚙️ .gitignore
├── 📝 README.md
└── 📄 requirements.txt
```

### 🎯 Target Audience
- Construction Site Managers
- Warehouse Safety Officers
- Manufacturing Compliance Teams

### Prerequisites

Ensure the following tools are installed before proceeding:

- Python 3.11.3  
- pyenv  
- pip  
- Git  

Make sure you have forked the repository before setting up the environment.


### Set up your Environment



#### **`macOS`** type the following commands : 

- For installing the virtual environment you can either use the [Makefile](Makefile) and run `make setup` or install it manually with the following commands:

     ```BASH
    make setup
    ```
    After that active your environment by following commands:
    ```BASH
    source .sscvenv/bin/activate
    ```
Or ....
- Install the virtual environment and the required packages by following commands:

    ```BASH
    pyenv local 3.11.3
    python -m venv .sscvenv
    source .sscvenv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    ```
    
#### **`WindowsOS`** type the following commands :

- Install the virtual environment and the required packages by following commands.

   For `PowerShell` CLI :

    ```PowerShell
    pyenv local 3.11.3
    python -m venv .sscvenv
    .sscvenv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    ```

    For `Git-bash` CLI :
  
    ```BASH
    pyenv local 3.11.3
    python -m venv .sscvenv
    source .sscvenv/Scripts/activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    ```

    **`Note:`**
    If you encounter an error when trying to run `pip install --upgrade pip`, try using the following command:
    ```Bash
    python.exe -m pip install --upgrade pip
    ```
