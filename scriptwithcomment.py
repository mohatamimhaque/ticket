# Standard library imports
import os, sys, time, re, ssl  

# Third-party libraries
import jwt, requests, aiohttp, asyncio, certifi  
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from colorama import Fore, init  

# Initialize colorama for auto color reset (ensures colored output works properly)
init(autoreset=True)  

# Load environment variables from .env file
load_dotenv()



# Load train booking details from environment variables
train_booking_info = {
    k: (int(v) if k in ["train_number", "seat"] else v.split(',') if k == "desired_seats" and v else v)
    for k, v in {
        "mobile_number": os.getenv("num"),
        "password": os.getenv("passcode"),
        "from_station": os.getenv("from_station"),
        "to_station": os.getenv("to_station"),
        "journey_date": os.getenv("journey_date"),
        "seat_class": os.getenv("seat_class"),
        "train_number": os.getenv("train_number"),
        "seat": os.getenv("seat"),
        "desired_seats": os.getenv("desired_seats")
    }.items()
}




def auth_token(num, passcode, max_retries=50):
    """
    Authenticate the user and retrieve an authentication token from the API.

    Args:
        num (str): The user's mobile number.
        passcode (str): The user's password.
        max_retries (int): Maximum number of retries in case of server errors. Default is 50.

    Returns:
        str: The authentication token if successful, otherwise None.
    """
    # API endpoint for authentication
    url = "https://railspaapi.shohoz.com/v1.0/app/auth/sign-in"
    
    # Payload containing the user's mobile number and password
    payload = {
        "mobile_number": num,
        "password": passcode  
    }

    retries = 0  # Counter to track the number of retries

    # Retry loop to handle server errors and request exceptions
    while retries < max_retries:
        try:
            # Send a POST request to the authentication endpoint
            res = requests.post(url, json=payload)  

            # Check if the request was successful (status code 200)
            if res.status_code == 200:
                # Parse the JSON response
                data = res.json()
                
                # Extract the token from the response
                token = data.get('data', {}).get('token')
                
                # If the token is found, print success message and return the token
                if token:
                    print(Fore.GREEN + "Success:")
                    print(Fore.GREEN + "Auth Token:", token)
                    return token
                else:
                    # If the token is not found in the response, print an error message
                    print(Fore.RED + "Failed to retrieve auth token from response.")
                    return None
            
            # Handle server errors (500, 502, 503, 504)
            elif res.status_code in [500, 502, 503, 504]:
                print(Fore.YELLOW + f"Server error {res.status_code}. Retrying in 1 second... ({retries + 1}/{max_retries})")
                time.sleep(1)  # Wait for 1 second before retrying
                retries += 1  # Increment the retry counter
            
            # Handle client-side errors (400, 401, etc.)
            else:
                print(Fore.RED + f"Error: {res.status_code} - {res.text}")
                return None  # Exit the function if it's a client-side error

        # Handle exceptions that occur during the request (e.g., network issues)
        except requests.RequestException as e:
            print(Fore.RED + f"Request error: {e}. Retrying in 1 second... ({retries + 1}/{max_retries})")
            time.sleep(1)  # Wait for 1 second before retrying
            retries += 1  # Increment the retry counter

    # If all retries are exhausted, print an error message and return None
    print(Fore.RED + "Max retries reached. Failed to obtain auth token.")
    return None


def extract_user_info(auth_key):
    """
    Extract user information (email, phone number, and name) from a JWT (JSON Web Token).

    Args:
        auth_key (str): The JWT token to decode.

    Returns:
        tuple: A tuple containing the user's email, phone number, and name.
               If decoding fails, returns (None, None, None).
    """
    try:
        # Decode the JWT token without verifying the signature
        decoded_token = jwt.decode(
            auth_key,
            options={"verify_signature": False},  # Skip signature verification
            algorithms=['RS256']  # Specify the algorithm used for the token
        )
    
        # Extract user information from the decoded token
        email = decoded_token.get("email", "")  # Get email or default to empty string
        phone = decoded_token.get("phone_number", "")  # Get phone number or default to empty string
        name = decoded_token.get("display_name", "")  # Get name or default to empty string

        # Print the extracted user information
        print(f"{Fore.CYAN}Email: {email}, Phone: {phone}, Name: {name}")

        # Return the extracted information as a tuple
        return email, phone, name

    except Exception as e:
        # Handle any exceptions that occur during token decoding
        print(f"{Fore.RED}Failed to decode auth token: {e}")
        # Return None for all fields if decoding fails
        return None, None, None
    

def fetch_trip_details(from_city, to_city, date, seat_class, train_number):
    """
    Fetch trip details (trip ID, route ID, boarding point ID, and train name) for a specific train and seat class.

    Args:
        from_city (str): The departure city.
        to_city (str): The destination city.
        date (str): The date of the journey in the required format.
        seat_class (str): The seat class (e.g., "SNIGDHA").
        train_number (str or int): The train number to search for.

    Returns:
        tuple: A tuple containing the trip ID, route ID, boarding point ID, and train name if found.
               If not found, the function will keep retrying until the details are available.
    """
    # API endpoint for fetching trip details
    url = "https://railspaapi.shohoz.com/v1.0/app/bookings/search-trips-v2"
    
    # Payload containing the search parameters
    payload = {
        "from_city": from_city,
        "to_city": to_city,
        "date_of_journey": date,
        "seat_class": seat_class
    }

    # Print a message indicating the start of the trip details fetching process
    print(f"{Fore.YELLOW}Fetching trip details for {from_city} to {to_city} on {date}...")

    # Infinite loop to keep retrying until trip details are found
    while True:
        try:
            # Send a GET request to the API with the search parameters
            response = requests.get(url, headers=headers, params=payload)
            
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Extract the list of trains from the response data
                data = response.json().get('data', {}).get('trains', [])

                # If no train data is available, retry after 1 second
                if not data:
                    print(f"{Fore.YELLOW}Trip details not available yet. Retrying in 1 second...")
                    time.sleep(1)
                    continue

                # Iterate through the list of trains to find the matching train number
                for train in data:
                    if train.get('train_model') == str(train_number):
                        # Iterate through the seat types to find the matching seat class
                        for seat in train.get('seat_types', []):
                            if seat.get("type") == seat_class:
                                # Extract trip details if the seat class matches
                                trip_id = seat.get('trip_id')
                                route_id = seat.get('trip_route_id')
                                boarding_id = train.get('boarding_points', [{}])[0].get("trip_point_id", None)
                                train_name = train.get("trip_number")

                                # Print the found trip details
                                print(f"{Fore.YELLOW}Trip details found! Train: {train_name}, Trip ID: {trip_id}, Route ID: {route_id}, Boarding Point ID: {boarding_id}")
                                
                                # Return the extracted trip details
                                return trip_id, route_id, boarding_id, train_name
                
                # If the train number or seat class is not found, retry after 1 second
                print(f"{Fore.YELLOW}Train Number {train_number} with seat class {seat_class} not available. Retrying in 1 second...")
                time.sleep(1)

            # Handle server errors (500, 502, 503, 504)
            elif response.status_code in [500, 502, 503, 504]:
                print(Fore.YELLOW + f"Server error {response.status_code}. Retrying in 1 second...")
                time.sleep(1)

            # Handle other HTTP errors
            else:
                print(Fore.RED + f"Failed to fetch trip details: {response.status_code} - {response.text}")
                print(f"{Fore.YELLOW}Server response: {response.text}")
                time.sleep(1)

        # Handle exceptions that occur during the request (e.g., network issues)
        except requests.RequestException as e:
            print(Fore.RED + f"Error during fetch trip details: {e}. Retrying in 1 second...")
            time.sleep(1)


async def is_booking_available():
    """
    Continuously checks if train booking is available by querying the seat layout API.

    Returns:
        dict: The seat layout data if booking is available, otherwise keeps retrying.
    """
    # API endpoint for fetching seat layout
    url = "https://railspaapi.shohoz.com/v1.0/app/bookings/seat-layout"
    
    # Payload containing trip details
    payload = {
        "trip_id": trip_id,
        "trip_route_id": route_id
    }

    # Minimum interval between retries to avoid overwhelming the server
    MIN_LOOP_INTERVAL = 0.001

    # Create an SSL context for secure connections
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Create a connector with the SSL context
    connector = aiohttp.TCPConnector(ssl_context=ssl_context)

    # Initialize start time for performance measurement
    start_time = time.perf_counter()

    # Create an asynchronous HTTP session
    async with aiohttp.ClientSession(connector=connector) as session:
        # Infinite loop to keep checking for booking availability
        while True:
            try:
                # Send a GET request to the seat layout API
                async with session.get(url, headers=headers, json=payload) as response:
                    # Calculate elapsed time since the start of the loop
                    end_time = time.perf_counter()
                    elapsed = end_time - start_time

                    # Check if the response status is 200 (success)
                    if response.status == 200:
                        # Parse the JSON response
                        data = await response.json()

                        # Check if "seatLayout" exists in the response data
                        if "seatLayout" in data.get("data", {}):
                            print(f"{Fore.GREEN}Booking is now available!")
                            return data["data"]["seatLayout"]  # Return the seat layout data

                    # Handle server errors (500, 501, 503, 504)
                    elif response.status in [500, 501, 503, 504]:
                        print(f"{Fore.YELLOW}Server overloaded (HTTP {response.status}). Retrying...")

                    # Handle client-side errors (422)
                    elif response.status == 422:
                        # Parse the error response
                        error_data = await response.json()
                        error_messages = error_data.get("error", {}).get("message", "")

                        # Extract the error message
                        if isinstance(error_messages, list):
                            error_message = error_messages[0]
                        elif isinstance(error_messages, dict):
                            error_message = error_messages.get("message", "")
                            error_key = error_messages.get("errorKey", "")
                        else:
                            error_message = "Unknown error"

                        # Print the server response for debugging
                        print(f"{Fore.CYAN}Server response: {error_data}")

                        # Handle specific error messages
                        if "ticket purchase for this trip will be available" in error_message:
                            print(f"{Fore.YELLOW}Booking is not open yet: {error_message}. Retrying...")
                            await asyncio.sleep(MIN_LOOP_INTERVAL)
                            continue

                        # Handle order limit exceeded error
                        if error_key == "OrderLimitExceeded":
                            print(f"{Fore.RED}Error: You have reached the maximum ticket booking limit for {train_booking_info['from_station']} to {train_booking_info['to_station']} on {train_booking_info['journey_date']}.")
                        else:
                            # Extract time information from the error message
                            time_match = re.search(r"(\d+)\s*minute[s]?\s*(\d+)\s*second[s]?", error_message, re.IGNORECASE)
                            if time_match:
                                minutes = int(time_match.group(1))
                                seconds = int(time_match.group(2))
                                total_seconds = minutes * 60 + seconds

                                # Format current and future times for display
                                current_time_formatted = time.strftime("%I:%M:%S %p", time.localtime())
                                future_time_formatted = time.strftime("%I:%M:%S %p", time.localtime(time.time() + total_seconds))

                                # Print the error message with time details
                                print(f"{Fore.RED}Error: {error_message} Current system time is {current_time_formatted}. Try again after {future_time_formatted}.")
                            else:
                                # Print a generic error message
                                print(f"{Fore.YELLOW}{error_message} Please try again later.")
                        exit()  # Exit the program if a critical error occurs

                    # Handle other HTTP errors
                    else:
                        print(f"{Fore.RED}Failed to fetch seat layout. HTTP: {response.status}")
                        text_resp = await response.text()
                        print(f"{Fore.CYAN}Server response: {text_resp}")

            # Handle exceptions that occur during the request (e.g., network issues)
            except aiohttp.ClientError as e:
                end_time = time.perf_counter()
                elapsed = end_time - start_time
                print(f"{Fore.RED}An error occurred while checking booking availability: {e}")

            # Ensure the loop runs at the specified minimum interval
            if elapsed < MIN_LOOP_INTERVAL:
                await asyncio.sleep(MIN_LOOP_INTERVAL - elapsed)


def find_selected_seats(seat_layout, desired_seats, max_seat):
    """
    Finds the selected seats based on the desired seat numbers.
    This assumes that `desired_seats` is a list of desired seat numbers.

    Args:
        seat_layout (list): The seat layout data from the API.
        desired_seats (list): A list of desired seat numbers.
        max_seat (int): The maximum number of seats to select.

    Returns:
        dict: A dictionary of selected seats with ticket IDs as keys and seat numbers as values.
    """
    selected_seats = {}

    # Look for seats matching desired seat numbers
    for coach in seat_layout:
        for row in coach['layout']:
            for seat in row:
                # Check if the seat is available and matches a desired seat number
                if seat['seat_availability'] == 1 and seat['seat_number'] in desired_seats:
                    selected_seats[seat['ticket_id']] = seat['seat_number']
                    # Stop if the maximum number of seats is reached
                    if len(selected_seats) == max_seat:
                        return selected_seats
    return selected_seats


def find_nearby_seats(seat_layout, desired_seats, max_seat):
    """
    Finds nearby seats based on available seats close to the desired ones.

    Args:
        seat_layout (list): The seat layout data from the API.
        desired_seats (list): A list of desired seat numbers.
        max_seat (int): The maximum number of seats to select.

    Returns:
        dict: A dictionary of selected seats with ticket IDs as keys and seat numbers as values.
    """
    selected_seats = {}

    for coach in seat_layout:
        for row in coach['layout']:
            # Filter available seats in the current row
            seat_numbers = [seat for seat in row if seat['seat_availability'] == 1]

            for desired_seat in desired_seats:
                # Find the desired seat in the available seats
                nearby_seats = [s for s in seat_numbers if s['seat_number'] == desired_seat]
                if nearby_seats:
                    desired_index = seat_numbers.index(nearby_seats[0])

                    # Find seats to the right of the desired seat
                    selected_seats = select_nearby_seats(selected_seats, seat_numbers, desired_index, max_seat, 1)
                    if len(selected_seats) == max_seat:
                        return selected_seats

                    # Find seats to the left of the desired seat
                    selected_seats = select_nearby_seats(selected_seats, seat_numbers, desired_index, max_seat, -1)
                    if len(selected_seats) == max_seat:
                        return selected_seats

    return selected_seats


def select_nearby_seats(selected_seats, seat_numbers, start_index, max_seat, direction):
    """
    Helper function to select nearby seats based on the given direction (left or right).

    Args:
        selected_seats (dict): A dictionary of already selected seats.
        seat_numbers (list): A list of available seats in the current row.
        start_index (int): The index of the desired seat in the seat_numbers list.
        max_seat (int): The maximum number of seats to select.
        direction (int): The direction to search for nearby seats (1 for right, -1 for left).

    Returns:
        dict: A dictionary of selected seats with ticket IDs as keys and seat numbers as values.
    """
    for offset in range(1, len(seat_numbers)):
        next_index = start_index + (offset * direction)
        if 0 <= next_index < len(seat_numbers):
            seat = seat_numbers[next_index]
            # Check if the seat is available and not already selected
            if seat['seat_availability'] == 1 and seat['seat_number'] not in selected_seats.values():
                selected_seats[seat['ticket_id']] = seat['seat_number']
                # Stop if the maximum number of seats is reached
                if len(selected_seats) == max_seat:
                    return selected_seats
    return selected_seats


def find_remaining_seats(seat_layout, selected_seats, max_seat):
    """
    Select remaining seats if the previously selected seats are not enough.

    Args:
        seat_layout (list): The seat layout data from the API.
        selected_seats (dict): A dictionary of already selected seats.
        max_seat (int): The maximum number of seats to select.

    Returns:
        dict: A dictionary of selected seats with ticket IDs as keys and seat numbers as values.
    """
    for coach in seat_layout:
        for row in coach['layout']:
            for seat in row:
                # Check if the seat is available and not already selected
                if seat['seat_availability'] == 1 and seat['seat_number'] not in selected_seats.values():
                    selected_seats[seat['ticket_id']] = seat['seat_number']
                    # Stop if the maximum number of seats is reached
                    if len(selected_seats) == max_seat:
                        return selected_seats
    return selected_seats


def find_seat_blocks(seat_layout, max_seat):
    """
    Finds contiguous blocks of available seats in the layout.

    Args:
        seat_layout (list): The seat layout data from the API.
        max_seat (int): The maximum number of seats to select.

    Returns:
        list: A list of available seat blocks, each containing a coach name and a list of seats.
    """
    all_available_seats = []
    for layout in seat_layout:
        coach_name = layout['floor_name']
        # Flatten the seat layout and filter available seats
        seats = [seat for row in layout['layout'] for seat in row if seat['seat_availability'] == 1]
        
        if seats:
            # Sort seats by seat number
            seats.sort(key=lambda x: int(x['seat_number'].split('-')[-1]))
            all_available_seats.append({'coach': coach_name, 'seats': seats})

    return all_available_seats


def get_ticket_id(seat_layout, desired_seats, max_seat):
    """
    Main function to select seats from the seat layout.

    Args:
        seat_layout (list): The seat layout data from the API.
        desired_seats (list): A list of desired seat numbers.
        max_seat (int): The maximum number of seats to select.

    Returns:
        dict: A dictionary of selected seats with ticket IDs as keys and seat numbers as values.
    """
    selected_seats = {}

    if desired_seats:
        # Step 1: Try to find exact matches for the desired seats
        selected_seats = find_selected_seats(seat_layout, desired_seats, max_seat)

        # Step 2: If not enough seats, try to find nearby seats
        if len(selected_seats) < max_seat:
            selected_seats = find_nearby_seats(seat_layout, desired_seats, max_seat)

        # Step 3: If still not enough seats, select any remaining available seats
        if len(selected_seats) < max_seat:
            selected_seats = find_remaining_seats(seat_layout, selected_seats, max_seat)

    else:
        # If no desired seats are provided, find contiguous blocks of seats
        all_available_seats = find_seat_blocks(seat_layout, max_seat)
        selected_seats = select_block_seats(all_available_seats, max_seat)

    if selected_seats:
        print(f"{Fore.YELLOW}Warning: Proceeding with {len(selected_seats)} instead of {max_seat}.")
        return selected_seats

    print(f"{Fore.RED} No seats available to proceed.")
    return None


def select_block_seats(all_available_seats, max_seat):
    """
    Selects contiguous block seats when no specific seat numbers are provided.

    Args:
        all_available_seats (list): A list of available seat blocks.
        max_seat (int): The maximum number of seats to select.

    Returns:
        dict: A dictionary of selected seats with ticket IDs as keys and seat numbers as values.
    """
    selected_seats = {}
    selected_seats_list = []

    for coach_data in all_available_seats:
        coach_name = coach_data['coach']
        seats = coach_data['seats']

        mid_index = len(seats) // 2
        for i in range(max(0, mid_index - max_seat), min(mid_index + 1, len(seats) - max_seat + 1)):
            block = seats[i:i + max_seat]
            seat_numbers = [int(seat['seat_number'].split('-')[-1]) for seat in block]

            # If seats form a contiguous block
            if max(seat_numbers) - min(seat_numbers) == max_seat - 1:
                for seat in block:
                    selected_seats[seat['ticket_id']] = seat['seat_number']

    for coach_data in all_available_seats:
        if len(selected_seats_list) >= max_seat:
            break

        coach_name = coach_data['coach']
        seats = coach_data['seats']

        left = mid_index - 1
        right = mid_index

        while len(selected_seats_list) < max_seat and (left >= 0 or right < len(seats)):
            if left >= 0 and len(selected_seats_list) < max_seat:
                selected_seats_list.append(seats[left])
                selected_seats[seats[left]['ticket_id']] = seats[left]['seat_number']
                left -= 1

            if right < len(seats) and len(selected_seats_list) < max_seat:
                selected_seats_list.append(seats[right])
                selected_seats[seats[right]['ticket_id']] = seats[right]['seat_number']
                right += 1

    return selected_seats   


async def reserve_seat():
    """
    Reserves seats based on the available seat layout and user preferences.
    This function waits for the seat layout to become available, selects seats,
    and attempts to reserve them.

    Returns:
        bool: True if seats are successfully reserved, otherwise False.
    """
    global ticket_ids
    
    # Print a message indicating the start of the seat reservation process
    print(f"{Fore.YELLOW}Waiting for seat layout availability...")

    # Wait for the seat layout to become available
    seat_layout = await is_booking_available()

    # If the seat layout is not available, exit the function
    if not seat_layout:
        print(f"{Fore.RED}Seat layout could not be retrieved. Exiting.")
        return False
    
    # Get the ticket IDs for the desired seats
    ticket_id_map = get_ticket_id(seat_layout, train_booking_info['desired_seats'], train_booking_info['seat'])

    # If no matching seats are found, exit the function
    if not ticket_id_map:
        print(f"{Fore.RED}No matching seats found based on desired preferences. Exiting...")
        return False
    
    # Store the ticket IDs and print the matched seat details
    ticket_ids = list(ticket_id_map.keys())
    print(f"{Fore.GREEN}Seats matched Details: {', '.join([f'{ticket_id_map[ticket]} (Ticket ID: {ticket})' for ticket in ticket_ids])}")

    # List to store successfully reserved ticket IDs
    successful_ticket_ids = []
    # Flag to stop further seat reservation if a limit is reached
    stop_reservation_due_to_limit = False

    def reserve_single_seat(ticket):
        """
        Reserves a single seat using the provided ticket ID.

        Args:
            ticket (str): The ticket ID of the seat to reserve.

        Returns:
            bool: True if the seat is successfully reserved, otherwise False.
        """
        nonlocal stop_reservation_due_to_limit
        # If the reservation limit has been reached, stop further reservations
        if stop_reservation_due_to_limit:
            return False
        
        # API endpoint for reserving a seat
        url = "https://railspaapi.shohoz.com/v1.0/app/bookings/reserve-seat"
        # Payload containing the ticket ID and route ID
        payload = {
            "ticket_id": ticket,
            "route_id": route_id
        }

        # Infinite loop to keep retrying until the seat is reserved or an error occurs
        while True:
            try:
                # Send a PATCH request to the API to reserve the seat
                response = requests.patch(url, headers=headers, json=payload)
                # Print the response from the API
                print(f"{Fore.CYAN}Response from Reserve Seat API for seat {ticket_id_map[ticket]} (Ticket ID: {ticket}): {response.text}")

                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    data = response.json()

                    # If the seat is successfully reserved, print a success message
                    if data['data'].get("ack") == 1:
                        print(f"{Fore.GREEN}Seat {ticket_id_map[ticket]} (Ticket ID: {ticket}) reserved successfully.")
                        successful_ticket_ids.append(ticket)
                        return True
                    else:
                        # If the seat reservation fails, print an error message
                        print(f"{Fore.RED}Failed to reserve seat {ticket_id_map[ticket]} (Ticket ID: {ticket}): {data}")
                        return False

                # Handle client-side errors (status code 422)
                elif response.status_code == 422:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("messages", {}).get("error_msg", "")
                    # If the maximum seat limit is reached, stop further reservations
                    if "Maximum 4 seats can be booked at a time" in error_msg:
                        print(f"{Fore.RED}Error: {error_msg}. Stopping further seat reservation.")
                        stop_reservation_due_to_limit = True
                        return False
                    # If the seat is no longer available, skip retrying
                    elif "Sorry! this ticket is not available now." in error_msg:
                        print(f"{Fore.RED}Seat {ticket_id_map[ticket]} (Ticket ID: {ticket}) is not available now. Skipping retry...")
                        return False
                # Handle server errors (status codes 500, 502, 503, 504)
                elif response.status_code in [500, 502, 503, 504]:
                    print(f"{Fore.YELLOW}Server Overloaded (HTTP {response.status_code}). Retrying in 100 milliseconds...")
                    time.sleep(0.1)
                # Handle other errors
                else:
                    print(f"{Fore.RED}Error: {response.status_code} - {response.text}")
                    return False
            
            # Handle exceptions that occur during the request (e.g., network issues)
            except Exception as e:
                print(f"{Fore.RED}Exception occurred while reserving seat {ticket_id_map[ticket]} (Ticket ID: {ticket}): {e}")
                time.sleep(0.1)
            

    # Print a message indicating the start of the seat reservation process
    print(f"{Fore.YELLOW}Initiating seat reservation process for {len(ticket_ids)} tickets...")

    # Use a ThreadPoolExecutor to reserve seats concurrently
    with ThreadPoolExecutor(max_workers=len(ticket_ids)) as executor:
        executor.map(reserve_single_seat, ticket_ids)

    # If seats are successfully reserved, update the ticket IDs and proceed
    if successful_ticket_ids:
        ticket_ids = successful_ticket_ids
        print(f"{Fore.GREEN}Successfully reserved tickets {ticket_ids}. Proceeding to next step...")
        return True
    else:
        # If no seats could be reserved, print an error message
        print(f"{Fore.RED}No seats could be reserved. Please try again...")
        return False
    

def send_passenger_details():
    """
    Sends passenger details to the API to initiate the OTP (One-Time Password) process.
    This function continuously retries in case of server errors or exceptions.

    Returns:
        bool: True if the OTP is sent successfully, otherwise False.
    """
    # API endpoint for sending passenger details
    url = "https://railspaapi.shohoz.com/v1.0/app/bookings/passenger-details"
    
    # Payload containing trip and ticket details
    payload = {
        "trip_id": trip_id,
        "trip_route_id": route_id,
        "ticket_ids": ticket_ids
    }

    # Infinite loop to keep retrying until the OTP is sent or an unrecoverable error occurs
    while True:
        try:
            # Send a POST request to the API with passenger details
            response = requests.post(url, headers=headers, json=payload)
            
            # Print the response from the API for debugging
            print(f"{Fore.CYAN}Response from Passenger Details API: {response.text}")

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                data = response.json()
                
                # Check if the OTP was sent successfully
                if data["data"]["success"]:
                    print(f"{Fore.GREEN}OTP sent successfully!")
                    return True  # OTP sent successfully
                else:
                    # If the OTP was not sent, print an error message
                    print(f"{Fore.RED}Failed to send OTP: {data}")
                    return False  # Failed to send OTP

            # Handle server errors (500, 502, 503, 504)
            elif response.status_code in [500, 502, 503, 504]:
                print(f"{Fore.YELLOW}Server Overloaded (HTTP {response.status_code}). Retrying in 1 second...")
                time.sleep(1)  # Wait for 1 second before retrying

            # Handle other HTTP errors
            else:
                print(f"{Fore.RED}Error: {response.status_code} - {response.text}")
                return False  # Exit if it's a client-side error (400, 401, etc.)

        # Handle exceptions that occur during the request (e.g., network issues)
        except requests.RequestException as e:
            print(f"{Fore.RED}Exception occurred while sending passenger details: {e}")
            time.sleep(1)  # Wait for 1 second before retrying

def send_passenger_details():
    """
    Sends passenger details to the API to initiate the OTP (One-Time Password) process.
    This function continuously retries in case of server errors or exceptions.

    Returns:
        bool: True if the OTP is sent successfully, otherwise False.
    """
    # API endpoint for sending passenger details
    url = "https://railspaapi.shohoz.com/v1.0/app/bookings/passenger-details"
    
    # Payload containing trip and ticket details
    payload = {
        "trip_id": trip_id,
        "trip_route_id": route_id,
        "ticket_ids": ticket_ids
    }

    # Infinite loop to keep retrying until the OTP is sent or an unrecoverable error occurs
    while True:
        try:
            # Send a POST request to the API with passenger details
            response = requests.post(url, headers=headers, json=payload)
            
            # Print the response from the API for debugging
            print(f"{Fore.CYAN}Response from Passenger Details API: {response.text}")

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                data = response.json()
                
                # Check if the OTP was sent successfully
                if data["data"]["success"]:
                    print(f"{Fore.GREEN}OTP sent successfully!")
                    return True  # OTP sent successfully
                else:
                    # If the OTP was not sent, print an error message
                    print(f"{Fore.RED}Failed to send OTP: {data}")
                    return False  # Failed to send OTP

            # Handle server errors (500, 502, 503, 504)
            elif response.status_code in [500, 502, 503, 504]:
                print(f"{Fore.YELLOW}Server Overloaded (HTTP {response.status_code}). Retrying in 1 second...")
                time.sleep(1)  # Wait for 1 second before retrying

            # Handle other HTTP errors
            else:
                print(f"{Fore.RED}Error: {response.status_code} - {response.text}")
                return False  # Exit if it's a client-side error (400, 401, etc.)

        # Handle exceptions that occur during the request (e.g., network issues)
        except requests.RequestException as e:
            print(f"{Fore.RED}Exception occurred while sending passenger details: {e}")
            time.sleep(1)  # Wait for 1 second before retrying



def prepare_confirm_payload(otp):
    user_email,user_phone,user_name = extract_user_info(token)
    if len(ticket_ids) > 1:
        passenger_names = [user_name]
        for i in range(1,len(ticket_ids)):
            passenger_name = input(f"{Fore.YELLOW}Enter passenger {i+1} name :")
            passenger_names.append(passenger_name)

        confirm_payload = {
            "is_bkash_online": True,
            "boarding_point_id": boarding_id,
            "from_city": train_booking_info['from_station'],
            "to_city": train_booking_info['to_station'],
            "date_of_journey": train_booking_info['journey_date'],
            "seat_class": train_booking_info['seat_class'],
            "passengerType": ["Adult"]*len(ticket_ids),
            "gender": ["male"] * len(ticket_ids),
            "pname": passenger_names,
            "pmobile": user_phone,
            "pemail": user_email,
            "trip_id": trip_id,
            "trip_route_id": route_id,
            "ticket_ids": ticket_ids,
            "contactperson": 0,
            "otp": otp,
            "selected_mobile_transaction": 1
        }
    else:
        confirm_payload = {
            "is_bkash_online": True,
            "boarding_point_id": boarding_id,
            "from_city": train_booking_info['from_station'],
            "to_city": train_booking_info['to_station'],
            "date_of_journey": train_booking_info['journey_date'],
            "seat_class": train_booking_info['seat_class'],
            "passengerType": ["Adult"],
            "gender": ["male"],
            "pname": [user_name],
            "pmobile": user_phone,
            "pemail": user_email,
            "trip_id": trip_id,
            "trip_route_id": route_id,
            "ticket_ids": ticket_ids,
            "contactperson": 0,
            "otp": otp,
            "selected_mobile_transaction": 1
        }

    return confirm_payload




def verify_and_confirm(otp):
    """
    Verifies the OTP and confirms the booking by selecting a payment method.
    This function handles OTP verification, payment method selection, and booking confirmation.

    Args:
        otp (str): The OTP entered by the user.

    Returns:
        bool: True if the booking is confirmed successfully, otherwise False.
    """
    # OTP Verification URL
    verify_url = "https://railspaapi.shohoz.com/v1.0/app/bookings/verify-otp"
    # Payload for OTP verification
    verify_payload = {
        "trip_id": trip_id,
        "trip_route_id": route_id,
        "ticket_ids": ticket_ids,
        "otp": otp
    }

    try:
        # Infinite loop to keep retrying until OTP is verified or an error occurs
        while True:
            # Send a POST request to verify the OTP
            response = requests.post(verify_url, headers=headers, json=verify_payload)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                data = response.json()
                # Check if OTP verification was successful
                if not data["data"]["success"]:
                    print(f"{Fore.RED}Failed to verify OTP: {data}")
                    return False  # OTP verification failed
                print(f"{Fore.GREEN}OTP verified Successfully!")
                break  # Exit the loop if OTP is verified

            # Handle server errors (500, 502, 503, 504)
            elif response.status_code in [500, 502, 503, 504]:
                print(f"{Fore.YELLOW}Server overloaded (HTTP {response.status_code}). Retrying in 1 second...")
                time.sleep(1)  # Wait for 1 second before retrying

            # Handle client-side errors (422)
            elif response.status_code == 422:
                data = response.json()
                error_info = data.get("error", {}).get("messages", {})

                # Extract error message and error key
                error_message = error_info.get("message", "Unknown error")
                error_key = error_info.get("errorKey", "Unknown errorkey")

                print(f"{Fore.RED}Error: {error_message} (Error Key: {error_key})")

                # If OTP is incorrect, prompt the user to enter the correct OTP
                if error_key == "OtpNotVerified":
                    otp = input(f"{Fore.YELLOW}The OTP does not match. Please enter correct OTP: ")
                    verify_payload["otp"] = otp  # Update the OTP in the payload
                else:
                    print(f"{Fore.RED}Error: {response.status_code} - {response.text}")
                    return False  # Exit if it's a client-side error

    # Handle exceptions that occur during OTP verification
    except Exception as e:
        print(f"{Fore.RED}Exception occurred: {e}")
        time.sleep(1)
        return False  # Exit if an exception occurs

    # Booking Confirmation URL
    confirm_url = "https://railspaapi.shohoz.com/v1.0/app/bookings/confirm"
    # Prepare the payload for booking confirmation
    confirm_payload = prepare_confirm_payload(otp)

    # Payment Method Selection
    print(f"\n{Fore.CYAN}Select Payment Method:")
    print(f"1. bKash\n2. Nagad\n3. Rocket\n4. Upay\n5. VISA\n6. Mastercard\n7. DBBL Nexus")

    # Loop to prompt the user to select a payment method
    while True:
        payment_choice = input(f"{Fore.YELLOW}Enter the number corresponding to your payment method: ")

        # Handle payment method selection
        if payment_choice == '1':  # bKash (default)
            print(f"{Fore.GREEN}Payment Method Selected: bKash")
            break
        elif payment_choice == '2':  # Nagad
            confirm_payload["is_bkash_online"] = False
            confirm_payload["selected_mobile_transaction"] = 3
            print(f"{Fore.GREEN}Payment Method Selected: Nagad")
            break
        elif payment_choice == '3':  # Rocket
            confirm_payload["is_bkash_online"] = False
            confirm_payload["selected_mobile_transaction"] = 4
            print(f"{Fore.GREEN}Payment Method Selected: Rocket")
            break
        elif payment_choice == '4':  # Upay
            confirm_payload["is_bkash_online"] = False
            confirm_payload["selected_mobile_transaction"] = 5
            print(f"{Fore.GREEN}Payment Method Selected: Upay")
            break
        elif payment_choice == '5':  # VISA
            confirm_payload["is_bkash_online"] = False
            confirm_payload.pop("selected_mobile_transaction", None)
            confirm_payload["pg"] = "visa"
            print(f"{Fore.GREEN}Payment Method Selected: VISA")
            break
        elif payment_choice == '6':  # Mastercard
            confirm_payload["is_bkash_online"] = False
            confirm_payload.pop("selected_mobile_transaction", None)
            confirm_payload["pg"] = "mastercard"
            print(f"{Fore.GREEN}Payment Method Selected: Mastercard")
            break
        elif payment_choice == '7':  # DBBL Nexus
            confirm_payload["is_bkash_online"] = False
            confirm_payload.pop("selected_mobile_transaction", None)
            confirm_payload["pg"] = "nexus"
            print(f"{Fore.GREEN}Payment Method Selected: DBBL Nexus")
            break
        else:
            print(f"{Fore.RED}Invalid selection! Please enter a number between 1 and 7.")

    # Booking Confirmation
    while True:
        # Send a PATCH request to confirm the booking
        response = requests.patch(confirm_url, headers=headers, json=confirm_payload)
        print(f"{Fore.CYAN}Response from Confirm Booking API: {response.text}")

        try:
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                data = response.json()
                # Check if the booking confirmation was successful
                if "redirectUrl" in data["data"]:
                    redirect_url = data["data"]["redirectUrl"]
                    print(f"\n{Fore.GREEN}{'='*50}")
                    print(f"{Fore.GREEN}Booking confirmed successfully!")
                    print(f"{Fore.YELLOW}IMPORTANT: Please note that this payment link can be used ONLY ONCE.")
                    print(f"{Fore.BLUE}Payment URL: {redirect_url}")
                    print(f"{Fore.GREEN}{'='*50}\n")
                    return True  # Booking confirmed successfully
                else:
                    print(f"{Fore.RED}Failed to confirm booking: {data}")
                    return False  # Booking confirmation failed

            # Handle server errors (500, 502, 503, 504)
            elif response.status_code in [500, 502, 503, 504]:
                print(f"{Fore.YELLOW}Server overloaded (HTTP {response.status_code}). Retrying in 1 second...")
                time.sleep(1)  # Wait for 1 second before retrying

            # Handle other errors
            else:
                print(f"{Fore.RED}Error: {response.status_code} - {response.text}")
                return False  # Exit if it's a client-side error

        # Handle exceptions that occur during booking confirmation
        except requests.RequestException as e:
            print(f"{Fore.RED}Exception occurred while confirming booking: {e}")
            time.sleep(1)
            return False  # Exit if an exception occurs
        




try:
    token = auth_token(train_booking_info.get('mobile_number', ''), train_booking_info.get('password', ''))
    if not token:
        print(f"{Fore.RED}Failed to fetch auth token. Exiting...")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    trip_id, route_id, boarding_id, train_name = fetch_trip_details(
        train_booking_info.get('from_station', ''),
        train_booking_info.get('to_station', ''),
        train_booking_info.get('journey_date', ''),
        train_booking_info.get('seat_class', ''),
        train_booking_info.get('train_number', '')
    )

    if not all([trip_id, route_id, boarding_id]):
        print(f"{Fore.RED}Error: Could not fetch trip details. Please check your inputs.")
        sys.exit(1)
    
    if  asyncio.run(reserve_seat()):  # Remove 'await' if the function is synchronous
        if send_passenger_details():
            print(f"{Fore.CYAN}Proceeding to OTP verification and confirmation...")
            
            otp = input(f"{Fore.YELLOW}Enter OTP received: ")
            if verify_and_confirm(otp):
                print(f"{Fore.GREEN}Booking Process completed Successfully!")
            else:
                print(f"{Fore.RED}Failed to complete booking process.")
        else:
            print(f"{Fore.RED}Failed to send passenger details and get OTP.")

    else:
        print(f"{Fore.RED}Failed to reserve the seat.")

except KeyError as e:
    print(f"{Fore.RED}Missing key in train_booking_info: {e}")
    sys.exit(1)

except Exception as e:
    print(f"{Fore.RED}An unexpected error occurred: {e}")
    sys.exit(1)
