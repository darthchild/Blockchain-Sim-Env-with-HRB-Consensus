import requests
import random
import concurrent.futures

g = 5
p = 29

def mod_exp(base, exp, mod):
    """Modular exponentiation function."""
    return pow(base, exp, mod)

# while(True):
#     # URLs to send requests to
#     URLS = ["http://127.0.0.1:5001", "http://127.0.0.1:5000", "http://127.0.0.1:5002"]

#     # Generate random user credentials
#     user_id_random = str(random.randint(0, 10000000))
#     password_random = random.randint(0, 10000000)

#     print(f"Initiating registration with user ID: {user_id_random} and password: {password_random}")
#     PARAMS = {"userId": user_id_random, "hashedPassword": password_random}

#     def send_request(url, endpoint, params):
#         """Send a POST request to the given URL + endpoint."""
#         try:
#             response = requests.post(f"{url}/{endpoint}", json=params)
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             print(f"Error connecting to {url}: {e}")
#             return None

#     def parallel_requests(endpoint, params):
#         """Send concurrent requests to all URLs."""
#         with concurrent.futures.ThreadPoolExecutor() as executor:
#             futures = {executor.submit(send_request, url, endpoint, params): url for url in URLS}
#             results = {}
#             for future in concurrent.futures.as_completed(futures):
#                 url = futures[future]
#                 try:
#                     results[url] = future.result()
#                 except Exception as e:
#                     print(f"Error with {url}: {e}")
#         return results

#     # Step 1: Register the user on all nodes
#     registration_results = parallel_requests("register", PARAMS)

#     # Find the first node that succeeded in registration
#     successful_node = next((url for url, result in registration_results.items() 
#                             if result and result.get('message') == "Registration successful"), None)

#     if successful_node:
#         print(f"Registration successful on node: {successful_node}")

#         # Step 2: Initiate ZKP on all nodes
#         ri = random.randint(1, p - 2)
#         T = mod_exp(g, ri, p)

#         print(f"Initiating ZKP with T: {T}")
#         PARAMS_ZKP = {"userId": user_id_random, "T": T}

#         zkp_results = parallel_requests("initiate_zkp", PARAMS_ZKP)

#         # Collect challenges from all nodes
#         challenges = {}
#         for url, result in zkp_results.items():
#             if result and 'challenge' in result:
#                 challenge = int(result['challenge'])
#                 challenges[url] = challenge
#                 print(f"Received challenge from {url}: {challenge}")

#         if challenges:
#             # Use the challenge from the first successful response (or combine challenges if needed)
#             selected_url, challenge = next(iter(challenges.items()))
#             print(f"Using challenge from {selected_url}: {challenge}")

#             # Step 3: Verify ZKP on all nodes
#             s = (ri + challenge * password_random) % (p - 1)
#             PARAMS_VERIFY = {"userId": user_id_random, "s": s, "challenge": challenge}

#             verify_results = parallel_requests("verify_zkp", PARAMS_VERIFY)

#             # Check if ZKP verification was successful on all nodes
#             for url, result in verify_results.items():
#                 if result and result.get('message') == "Login successful":
#                     print(f"ZKP verification successful on {url}.")
#                 else:
#                     print(f"ZKP verification failed on {url}.")
#                     break
#         else:
#             print("Failed to retrieve challenges from ZKP initiation.")
#             break
#     else:
#         print("Registration failed on all nodes.")
#         break

# URLs to send requests to
URLS = ["http://127.0.0.1:5001", "http://127.0.0.1:5000", "http://127.0.0.1:5002"]

# Generate random user credentials
user_id_random = str(random.randint(0, 10000000))
password_random = random.randint(0, 10000000)

print(f"Initiating registration with user ID: {user_id_random} and password: {password_random}")
PARAMS = {"userId": user_id_random, "hashedPassword": password_random}

def send_request(url, endpoint, params):
    """Send a POST request to the given URL + endpoint."""
    try:
        response = requests.post(f"{url}/{endpoint}", json=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to {url}: {e}")
        return None

def parallel_requests(endpoint, params):
    """Send concurrent requests to all URLs."""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(send_request, url, endpoint, params): url for url in URLS}
        results = {}
        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                results[url] = future.result()
            except Exception as e:
                print(f"Error with {url}: {e}")
    return results

# Step 1: Register the user on all nodes
registration_results = parallel_requests("register", PARAMS)

# Find the first node that succeeded in registration
successful_node = next((url for url, result in registration_results.items() 
                        if result and result.get('message') == "Registration successful"), None)

if successful_node:
    print(f"Registration successful on node: {successful_node}")

    # Step 2: Initiate ZKP on all nodes
    ri = random.randint(1, p - 2)
    T = mod_exp(g, ri, p)

    print(f"Initiating ZKP with T: {T}")
    PARAMS_ZKP = {"userId": user_id_random, "T": T}

    zkp_results = parallel_requests("initiate_zkp", PARAMS_ZKP)

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
        print(f"Using challenge from {selected_url}: {challenge}")

        # Step 3: Verify ZKP on all nodes
        s = (ri + challenge * password_random) % (p - 1)
        PARAMS_VERIFY = {"userId": user_id_random, "s": s, "challenge": challenge}

        verify_results = parallel_requests("verify_zkp", PARAMS_VERIFY)

        # Check if ZKP verification was successful on all nodes
        for url, result in verify_results.items():
            if result and result.get('message') == "Login successful":
                print(f"ZKP verification successful on {url}.")
            else:
                print(f"ZKP verification failed on {url}.")
    else:
        print("Failed to retrieve challenges from ZKP initiation.")
else:
    print("Registration failed on all nodes.")
