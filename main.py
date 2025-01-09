import requests
import time

def load_api_keys(api_keys_file):
    """Load API keys from a file."""
    try:
        with open(api_keys_file, "r", encoding="utf-8") as file:
            keys = [line.strip() for line in file.readlines() if line.strip()]
        if not keys:
            print("Error: API keys file is empty. Please provide valid API keys.")
            return []
        return keys
    except FileNotFoundError:
        print(f"Error: {api_keys_file} not found. Please provide a valid file.")
        return []

def google_dorking(api_keys, targets, dorks_file, output_file, results_per_page=10):
    url = "http://api.serpstack.com/search"
    global_key_index = 0  # Start with the first API key

    try:
        print(f"Reading dorks from {dorks_file}...")
        with open(dorks_file, "r", encoding="utf-8") as file:
            dorks = [line.strip() for line in file.readlines() if line.strip()]

        if not dorks:
            print("No dorks found in the file. Please ensure the file is not empty.")
            return

        print("Google Dorking Results")
        print("=" * 50)

        # Open the output file for writing results
        with open(output_file, "w", encoding="utf-8") as output:
            output.write("Google Dorking Results\n")
            output.write("=" * 50 + "\n")

            for dork in dorks:
                target_query = " OR ".join([f"site:({target})" for target in targets])
                search_query = f"{dork} {target_query}"  # Combine dork with target query
                success = False
                retries = 0

                while retries < len(api_keys) and not success:
                    if global_key_index >= len(api_keys):
                        print("All API keys have been exhausted. Terminating.")
                        output.write("All API keys have been exhausted. Terminating.\n")
                        return  # Stop processing further dorks

                    api_key = api_keys[global_key_index]
                    print(f"Using API Key: {api_key}")

                    params = {
                        "access_key": api_key,
                        "query": search_query,
                        "num": results_per_page
                    }

                    try:
                        response = requests.get(url, params=params, timeout=10)  # Add timeout
                        if response.status_code == 200:
                            result = response.json()

                            if not result.get("success", True):
                                error_code = result.get("error", {}).get("code", "")
                                error_info = result.get("error", {}).get("info", "")

                                if error_code == 104:  # Monthly usage limit reached
                                    print(f"Monthly usage limit reached for key {api_key}. Switching to the next API key...")
                                    global_key_index += 1
                                    retries += 1
                                    continue

                                elif error_code == 429:  # Rate limit exceeded
                                    print(f"Rate limit exceeded for key {api_key}. Retrying after 1 minute...")
                                    time.sleep(60)
                                    continue

                                else:  # Unhandled error
                                    print(f"Unhandled error: {error_info}")
                                    output.write(f"Unhandled error: {error_info}\n")
                                    global_key_index += 1
                                    retries += 1
                                    continue

                            # Process successful response
                            if result.get("success", True):
                                print(f"Dork: {search_query}")
                                output.write(f"Dork: {search_query}\n")

                                if "organic_results" in result:
                                    print("Links:")
                                    output.write("Links:\n")
                                    for item in result.get("organic_results", []):
                                        link = item.get("url", "No Link")
                                        print(link)
                                        output.write(f"{link}\n")
                                else:
                                    print(f"No results returned for this query: {search_query}")
                                    output.write(f"No results returned for this query: {search_query}\n")

                                success = True  # Exit loop for this dork
                        else:
                            print(f"HTTP Error: {response.status_code} for query: {search_query}")
                            global_key_index += 1
                            retries += 1
                            continue

                    except requests.exceptions.Timeout:
                        print(f"Timeout error for key {api_key}. Retrying...")
                        retries += 1
                        continue
                    except requests.exceptions.RequestException as e:
                        print(f"Request failed: {e}")
                        output.write(f"Request failed: {e}\n")
                        retries += 1
                        continue

                print("=" * 50)
                output.write("=" * 50 + "\n")
                print("Waiting for 1 seconds before processing the next dork...")
                time.sleep(1)  # Delay between dorks

    except FileNotFoundError:
        print(f"Error: {dorks_file} not found. Please provide a valid file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    API_KEYS_FILE = "api_keys.txt"
    OUTPUT_FILE = "results.txt"

    # Load API keys from the external file
    api_keys = load_api_keys(API_KEYS_FILE)

    if api_keys:
        target_input = input("Enter target domains (comma-separated, e.g., target1.com,target2.com): ").strip()
        targets = [t.strip() for t in target_input.split(",") if t.strip()]
        dorks_file = input("Enter the dorks file path (e.g., dorks.txt): ").strip()

        if targets and dorks_file:
            results_per_page = 50  # Set the desired number of results per page
            google_dorking(api_keys, targets, dorks_file, OUTPUT_FILE, results_per_page)
        else:
            print("Error: Both target domains and dorks file must be provided.")
