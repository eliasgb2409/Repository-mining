import requests
import datetime as dt

# Just add your github token in <GITHUB TOKEN>
HEADERS = {'Accept': 'application/vnd.github+json',
           'Authorization': 'Bearer <GITHUB TOKEN>',
           'X-GitHub-Api-Version': '2022-11-28'
           }

COPILOT_RELEASE_DATE = dt.date(2021, 10, 29)

# Function that retreives all repos within a GitHub organization
# that has been at least active since the official release of Copilot
def get_all_repos(org):

    repo_names = set()
    full_path = f"./data/new_{org}_path_names.txt"
    
    page = 1
        
    # Retrieve repo names through API if we haven't done this before
    with open(full_path, "a") as file:
        start_date = dt.date(2022, 9, 1)
        
        # The GitHub API can only provide a maximum of 100 repos per page, so must iterate over all pages in pagination
        while True:
            url = f"https://api.github.com/orgs/{org}/repos?per_page=100&page={page}"  
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code != 200:
                print(f"Error fetching repos: {response.status_code}")
                break
            
            repos = response.json()
            if not repos: 
                break  # No more repos, go out of lopp
            
            print(f"Loading in repo names from page {page}...")                    
            for repo in repos:
                # Check if repo has been active since at least (september 1, 2024)
                pushed_date = dt.datetime.strptime(repo["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").date()
                
                # Add repo to our set if repo has been active within our timeframe
                if pushed_date >= start_date:  
                    print(f"Repo last updated {repo["pushed_at"]}")
                    full_repo_path = f"https://github.com/{repo["full_name"]}.git"
                    repo_names.add(full_repo_path)
                    file.write(f"{full_repo_path}\n")

            page += 1 # Gå til neste side av pagnation
            
        print("Alle repoer lastet ned.")
        print("Antall repoer:", len(repo_names))