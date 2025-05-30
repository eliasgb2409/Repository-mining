import datetime as dt
import pandas as pd
import os
from pydriller import Repository
import json
import csv
import time
from tqdm import tqdm

# Global values
copilot_date = dt.datetime(2023, 9, 1)
date_from = dt.datetime(2022, 9, 1)
date_to = dt.datetime(2024, 9, 1)


def merge_commit_data(file1, file2):
    """For merging nais and navikt commmit files"""

    timestr = time.strftime("%Y%m%d")
    output_folder = "data"
    os.makedirs(output_folder, exist_ok=True)  
    csv_output_filename = os.path.join(output_folder, f"{timestr}_default_branch_merged_commit_stats.csv")
        
    # Read the CSV files
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    
    # Concatenate the dataframes
    combined_df = pd.concat([df1, df2], ignore_index=True)

    # Save the merged dataframe as a new CSV file
    combined_df.to_csv(csv_output_filename, index=False)
    
    print(f"Combined data saved as {csv_output_filename}")
    
    return combined_df



def continue_from_last_processed_repo(csv_output_filepath, target_repos, org):
    """Function for continuing from last processed repo incease of a crash"""

    try:
        # Read the csv file we're writing commit data to, so that we can find the last processed repo
        df_commits = pd.read_csv(csv_output_filepath)
    except FileNotFoundError:
        print("No existing CSV found. Starting from scratch.")
        return target_repos
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return target_repos

    if df_commits.empty:
        print("CSV is empty. Starting from the beginning.")
        return target_repos
    
    # Name of the last processed repo 
    last_repo_processed = df_commits['Repository'].values[-1]
    print(f'Last processed repo: {last_repo_processed}')

    # Index 
    index = 0
    for repo_path in target_repos:
        # Get the repo name of the repo path we currenly are on to match with the repo name that was last processed in the csv-file
        repo_name = repo_path.split(f"github.com/{org}/")[-1].replace(".git", "")
        #print(repo_name)
        
        # If we find a match we get the index of that repo, and use that index to slice the list of target_repos from the index of the last repo we processed
        if(repo_name.strip() == last_repo_processed.strip()):
            print("Match!")
            last_repo_index = target_repos.index(repo_path)
            index = last_repo_index

    # List of remaning 
    remaining_repos = target_repos[index:]
    return remaining_repos



def read_json_usernames(filepath="./data/username_fullname.json"):
    """Reading json file to get usernames and their correspondings 
    full names (author names).
    """

    with open(filepath, "r", encoding="utf-8") as file:
        data_dict = json.load(file)
        return data_dict



def repo_file_to_set(full_path):
    """Get list of all repo names that we are analyzing"""

    
    if os.path.exists(full_path):
        df = pd.read_csv(full_path, header=None, names=["repo_name"])
        repo_names = df["repo_name"].tolist()
    
    return repo_names 

 
 
def get_copilot_users(file_path):
    """Retreive all copilot users based on survey responses"""
    
    df = pd.read_excel(file_path, sheet_name="Values")
    
    copilot_users = df.loc[
        (df["GitHub Copilot i NAV : Bruker du, eller har du brukt, GitHub Copilot?"] == "Ja") &
        df["GitHub-metrikker : GitHub-brukernavn (valgfritt):"].notna() &
        (df["GitHub-metrikker : GitHub-brukernavn (valgfritt):"] != ""),
        "GitHub-metrikker : GitHub-brukernavn (valgfritt):", 
    ].tolist()
    
    copilot_users = [user.strip() for user in copilot_users]
    return set(copilot_users) 



def is_copilot_user(username):
    """Function to check wether a user is a copilot user or not"""

    survey_results_filepath = "./data/mock_survey_results.xlsx"
    copilot_users = get_copilot_users(survey_results_filepath)
    
    if username.strip() in copilot_users:
        return True
    else:
        return False



def process_commits(target_repos, username_mapping, org):
    """Performs the repository mining and saves data into 
    csv-file.

    Args:
        target_repos (lst(str)): list of repositories we are mining
        username_mapping (dict): Dictionary of username and corresponding author name(s)
        org (str): organization name

    Returns:
        dataframe: dataframe of the repository
        str: filepath to the csv file containing the commit data
    """
    commit_records = []
    
    # Define CSV file path
    timestr = time.strftime("%Y%m%d")
    output_csv_filename = f"{timestr}_main_branch_{org}_commit_stats.csv"
    path = "./data/"
    os.makedirs(path, exist_ok=True)  # Ensure directory exists
    csv_filepath = os.path.join(path, output_csv_filename)

    # Define CSV column headers
    fieldnames = [
        "User", "Copilot user", "Author name", "Author email", "Date", "Repository",
        "Insertions", "Deletions", "Total lines", "Files changed",
        "Unit size (DMM)", "Complexity (DMM)", "Interface (DMM)", "Commits", "Commit hash",
        "Copilot period", "Merge commit", "Default branch", "Org"
    ]

    # Map fullname to username 
    author_to_username = {}
    authors = []

    # Creates a reverse lookup so later if you see "John Smith" in a commit, you can get "johnsmith" as the username in the csv file
    # This makes all commits with of a user with mulitple author names linked to that username 
    for username, fullname_list in username_mapping.items():
        username = username.strip()
        for fullname in fullname_list:
            fullname = fullname.strip()
            author_to_username[fullname] = username
            if(fullname not in authors):
                authors.append(fullname)
    
    print(f"\nReverse mapping: {author_to_username}")
    print(f"\nAuthors: {authors}")
            
    file_exists = os.path.exists(csv_filepath)
    
    # Read existing data to find already processed commit hashes
    if file_exists:
        existing_df = pd.read_csv(csv_filepath)
        if not existing_df.empty:
            print("CSV contains commit data. Continuing from last time.")
            #processed_commit_hashes = set(existing_df["Commit hash"].values)
        else:
            print("CSV is empty. Starting fresh.")
    else:
        print("No CSV file found. Starting from scratch.")
        
        
    remaining_repos = continue_from_last_processed_repo(csv_filepath, target_repos, org)
    print(f"Remaining repos to process: {len(remaining_repos)}. Starting with {remaining_repos[0]}.")
    
    with open(csv_filepath, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Write header if the file is newly created
        if not file_exists:
            writer.writeheader()
            
        for repo in tqdm(remaining_repos, colour="green"):
            # Process commits for users
            # We ignore merge commits, skip whitespaces and only look at commits from default branch - that is either "master" or "main" depending on their set name
            # Histogram is also chosen as the diff algorithm as it's preffered when analyzing code changes 
            
            # https://accessibleai.dev/post/extracting-git-data-pydriller/
            for commit in Repository(path_to_repo=repo, since=date_from, to=date_to, 
                                    only_authors=authors, only_no_merge=True, skip_whitespaces=True, histogram_diff=True).traverse_commits():
                
                full_name = commit.author.name
                
                # Map full name to username 
                github_username = author_to_username.get(full_name.strip(), "Unknown")

                # Check if user is copilot user
                copilot_user = is_copilot_user(github_username)
                
                print(f"Reading repo {commit.project_name} for user {github_username}")
                
                record = {
                    "User": github_username,  # Always use the consistent GitHub username
                    "Copilot user": copilot_user,
                    "Author name": full_name,  # Original name from commit
                    "Author email": commit.author.email,
                    "Date": commit.committer_date.date(),
                    "Repository": commit.project_name, 
                    "Insertions": commit.insertions,
                    "Deletions": commit.deletions,
                    "Total lines": commit.lines,
                    "Files changed": commit.files,
                    "Unit size (DMM)": commit.dmm_unit_size,
                    "Complexity (DMM)": commit.dmm_unit_complexity,
                    "Interface (DMM)": commit.dmm_unit_interfacing,
                    "Commits": 1,
                    "Commit hash": commit.hash,
                    "Copilot period": "after" if commit.committer_date.date() >= copilot_date.date() else "before",
                    "Merge commit": commit.merge,
                    "Default branch": commit.in_main_branch,
                    "Org": org
                }
                
                commit_records.append(record)
                writer.writerow(record)
    
    # Convert the list of records into a DataFrame and save to CSV
    df = pd.DataFrame(commit_records)
    print(f"***CSV file saved as {output_csv_filename} in {path}.***")
    
    # Return the DataFrame for further analysis if needed
    return df, csv_filepath


if __name__ == "__main__":
    # This is how it would be performed when performing the repo mining on navikt and nais:
    
    # Standardized mapping structure
    # username_mapping = read_json_usernames()

    # # List of repositories to analyze
    # nav_repo_path = "./data/new_navikt_path_names.txt"
    # nav_target_repos = repo_file_to_set(nav_repo_path)
    
    # nais_repo_path = "./data/new_nais_path_names.txt"
    # nais_target_repos = repo_file_to_set(nais_repo_path)
    
    # # Process the commits
    # nav_df, nav_output_filename = process_commits(nav_target_repos, username_mapping, "navikt")
    # nais_df, nais_output_filename = process_commits(nais_target_repos, username_mapping, "nais")
    
    # # Merge commit data to a single file
    # merge_commit_data(nav_output_filename, nais_output_filename)
    
    # However this is how we do it to demonstrate:
    
    username_mapping = {"andrewyng":["Andrew Ng"]}

    # List of repositories to analyze
    test_repo_paths = ["https://github.com/andrewyng/aisuite"]
    
    test_org_name = "Test"
    
    # Process the commits
    test_df, test_output_filename = process_commits(test_repo_paths, username_mapping, test_org_name)