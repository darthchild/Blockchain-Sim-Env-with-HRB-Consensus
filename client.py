# client.py

import requests
import random
import concurrent.futures
import time

g = 5
p = 29

def mod_exp(base, exp, mod):
    """Modular exponentiation function."""
    return pow(base, exp, mod)

def send_request(url, endpoint, params):
    """Send a POST request to the given URL + endpoint."""
    try:
        response = requests.post(f"{url}/{endpoint}", json=params, timeout=100)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to {url}: {e}")
        return None

def parallel_requests(endpoints, params, urls):
    """Send concurrent requests to all URLs for specified endpoints."""
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
        future_to_url = {executor.submit(send_request, url, endpoints, params): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results[url] = future.result()
            except Exception as e:
                print(f"Error with {url}: {e}")
    return results

def main():
    # Configuration
    number_of_nodes = 10  # Should match the number used in deploy_nodes.py
    starting_port = 5000
    URLS = [f"http://127.0.0.1:{port}" for port in range(starting_port, starting_port + number_of_nodes)]

    # Generate random user credentials
    user_id_random = str(random.randint(0, 10000000))
    password_random = random.randint(0, 10000000)

    print(f"\nInitiating registration with user ID: {user_id_random} and password: {password_random}")
    PARAMS = {"userId": user_id_random, "hashedPassword": password_random}

    # Step 1: Register the user on all nodes
    registration_results = parallel_requests("register", PARAMS, URLS)

    # Find the first node that succeeded in registration
    successful_node = next((url for url, result in registration_results.items() 
                            if result and result.get('message') == "Registration successful"), None)

    if successful_node:
        print(f"\nRegistration successful on node: {successful_node}")

        # Step 2: Initiate ZKP on all nodes
        ri = random.randint(1, p - 2)
        T = mod_exp(g, ri, p)

        print(f"\nInitiating ZKP with T: {T}")
        PARAMS_ZKP = {"userId": user_id_random, "T": T}

        zkp_results = parallel_requests("initiate_zkp", PARAMS_ZKP, URLS)

        # Collect challenges from all nodes
        challenges = {}
        for url, result in zkp_results.items():
            if result and 'challenge' in result:
                challenge = int(result['challenge'])
                challenges[url] = challenge
                print(f"Received challenge from {url}: {challenge}")

        if challenges:
            # Use the challenge from the first successful response (or combine challenges if needed)
            selected_url, challenge = next(iter(challenges.items()))
            print(f"\nUsing challenge from {selected_url}: {challenge}")

            # Step 3: Verify ZKP on all nodes
            s = (ri + challenge * password_random) % (p - 1)
            PARAMS_VERIFY = {"userId": user_id_random, "s": s, "challenge": challenge}

            verify_results = parallel_requests("verify_zkp", PARAMS_VERIFY, URLS)

            # Check if ZKP verification was successful on all nodes
            success_count = 0
            for url, result in verify_results.items():
                if result and result.get('message') == "Login successful":
                    print(f"ZKP verification successful on {url}.")
                    success_count += 1
                else:
                    print(f"ZKP verification failed on {url}.")

            print(f"\nTotal successful verifications: {success_count}/{number_of_nodes}")
        else:
            print("\nFailed to retrieve challenges from ZKP initiation.")
    else:
        print("\nRegistration failed on all nodes.")

if __name__ == "__main__":
    main()
