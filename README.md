# Repository-mining

Scripts for mining Git repositories, cleaning data, and generating plots for analysis in a Copilot case study.

## Assumptions

These scripts assume you are using **survey data** alongside the Git data. In our case, the survey helped us:

- Identify Copilot users and non-users  
- Determine users' roles and usernames  
- Get perceived productivity changes using a 5-point Likert score  

Many parts of the scripts depend on this survey data. For example, during repository mining, the author of a commit is mapped to a username from the survey and then checked if they use Copilot.

You can modify or remove this survey-related logic to fit your own data.

## Guide

After cloning the repo sucessfully, before running any scripts, install the required packages in your virtualenv.

```bash
pip install -r requirements.txt
```

### Folder structure

#### `data/`
Contains:

- Anonymized commit data from NAV IT and NAIS  
- Anonymized survey data with roles, usernames, Copilot usage status, and Likert scores for perceived productivity  

#### `plots/`
Contains:

- Subfolders with multiple individual plots by category  
- Additional standalone plots  

### Scripts

- `analyze_default_commits(cleaned).ipynb`: A Jupyter Notebook for:
  - Loading and cleaning data  
  - Aggregating metrics  
  - Creating plots for analysis  

- `py_driller_commits.py`: Script for mining Git repositories  

- `get_repos.py`: Helper script to fetch repositories from a GitHub organization  

- `sample_tests.ipynb`: Another helper notebook for fetching repositories  

## Analytical Scenarios (after repository mining)

### 1. Activity Differences Between Copilot Users and Non-users

- Calculate average weekly activity (insertions, deletions, commit frequency) from 2022-09-01 to 2024-09-01  
- Compare trends before and after Copilot introduction  

### 2. Correlation of Activity Metrics and Perceived Productivity (Copilot Users)

- Analyze how activity metrics (insertions, deletions, commits, etc.) relate to each other within the SPACE framework  
- Examine how these metrics relate to perceived productivity changes from the survey 

### Note

Since our data results are anonymized, we have **removed any username mapping files** and **repository name files** from the repository.

In the script `py_driller_commits.py`, at the bottom of the file, there are several lines of code that are commented out — these are the lines we used to generate our commit data. You are welcome to modify and run the script with your own parameters.

However, please note that **reproducing our full results requires processing a large number of repositories**, which can take **several hours** to complete.

To provide a quick demonstration of how the script works, we’ve included a test configuration below the commented-out code. This uses the **public GitHub profile and repository of Andrew Ng** ([https://github.com/andrewyng](https://github.com/andrewyng)) as an example. The test output generated from this run is stored in the `data/` folder.
