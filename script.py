import os, sys, time, re, ssl  
import jwt, requests, aiohttp, asyncio, certifi  
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from colorama import Fore, init
import webbrowser



init(autoreset=True)  
load_dotenv()
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
    url = "https://railspaapi.shohoz.com/v1.0/app/auth/sign-in"
    payload = {
        "mobile_number": num,
        "password": passcode
    }
    retries = 0
    while retries < max_retries:
        try:
            res = requests.post(url, json=payload)
            if res.status_code == 200:
                data = res.json()
                token = data.get('data', {}).get('token')
                if token:
                    print(Fore.GREEN + "Success:")
                    print(Fore.GREEN + "Auth Token:", token)
                    return token
                else:
                    print(Fore.RED + "Failed to retrieve auth token from response.")
                    return None
            elif res.status_code in [500, 502, 503, 504]:
                print(Fore.YELLOW + f"Server error {res.status_code}. Retrying in 1 second... ({retries + 1}/{max_retries})")
                time.sleep(1)
                retries += 1
            else:
                print(Fore.RED + f"Error: {res.status_code} - {res.text}")
                return None
        except requests.RequestException as e:
            print(Fore.RED + f"Request error: {e}. Retrying in 1 second... ({retries + 1}/{max_retries})")
            time.sleep(1)
            retries += 1
    print(Fore.RED + "Max retries reached. Failed to obtain auth token.")
    return None
token = auth_token(train_booking_info.get('mobile_number', ''), train_booking_info.get('password', ''))
headers = {"Authorization": f"Bearer {token}"}
def main():
    def extract_user_info(auth_key):
        try:
            decoded_token = jwt.decode(
                auth_key,
                options={"verify_signature": False},  
                algorithms=['RS256']  
            )
            email = decoded_token.get("email", "")  
            phone = decoded_token.get("phone_number", "")  
            name = decoded_token.get("display_name", "")  
            print(f"{Fore.CYAN}Email: {email}, Phone: {phone}, Name: {name}")
            return email, phone, name
        except Exception as e:
            print(f"{Fore.RED}Failed to decode auth token: {e}")
            return None, None, None
    def fetch_trip_details(from_city, to_city, date, seat_class, train_number):
        url = "https://railspaapi.shohoz.com/v1.0/app/bookings/search-trips-v2"
        payload = {
            "from_city": from_city,
            "to_city": to_city,
            "date_of_journey": date,
            "seat_class": seat_class
        }
        print(f"{Fore.YELLOW}Fetching trip details for {from_city} to {to_city} on {date}...")
        while True:
            try:
                response = requests.get(url, headers=headers, params=payload)
                if response.status_code == 200:
                    data = response.json().get('data', {}).get('trains', [])
                    if not data:
                        print(f"{Fore.YELLOW}Trip details not available yet. Retrying in 1 second...")
                        time.sleep(1)
                        continue
                    for train in data:
                        if train.get('train_model') == str(train_number):
                            for seat in train.get('seat_types', []):
                                if seat.get("type") == seat_class:
                                    trip_id = seat.get('trip_id')
                                    route_id = seat.get('trip_route_id')
                                    boarding_id = train.get('boarding_points', [{}])[0].get("trip_point_id", None)
                                    train_name = train.get("trip_number")
                                    print(f"{Fore.YELLOW}Trip details found! Train: {train_name}, Trip ID: {trip_id}, Route ID: {route_id}, Boarding Point ID: {boarding_id}")
                                    return trip_id, route_id, boarding_id, train_name
                    print(f"{Fore.YELLOW}Train Number {train_number} with seat class {seat_class} not available. Retrying in 1 second...")
                    time.sleep(1)
                elif response.status_code in [500, 502, 503, 504]:
                    print(Fore.YELLOW + f"Server error {response.status_code}. Retrying in 1 second...")
                    time.sleep(1)
                else:
                    print(Fore.RED + f"Failed to fetch trip details: {response.status_code} - {response.text}")
                    print(f"{Fore.YELLOW}Server response: {response.text}")
                    time.sleep(1)
            except requests.RequestException as e:
                print(Fore.RED + f"Error during fetch trip details: {e}. Retrying in 1 second...")
                time.sleep(1)
    async def is_booking_available():
        url = "https://railspaapi.shohoz.com/v1.0/app/bookings/seat-layout"
        payload = {
            "trip_id": trip_id,
            "trip_route_id": route_id
        }
        MIN_LOOP_INTERVAL = 0.001
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl_context=ssl_context)
        start_time = time.perf_counter()
        async with aiohttp.ClientSession(connector=connector) as session:
            while True:
                try:
                    async with session.get(url, headers=headers, json=payload) as response:
                        end_time = time.perf_counter()
                        elapsed = end_time - start_time
                        if response.status == 200:
                            data = await response.json()
                            if "seatLayout" in data.get("data", {}):
                                print(f"{Fore.GREEN}Booking is now available!")
                                return data["data"]["seatLayout"]  
                        elif response.status in [500, 501, 503, 504]:
                            print(f"{Fore.YELLOW}Server overloaded (HTTP {response.status}). Retrying...")
                        elif response.status == 422:
                            error_key = None
                            error_data = await response.json()
                            error_messages = error_data.get("error", {}).get("messages", "")
                            if isinstance(error_messages, list):
                                error_message = error_messages[0]
                            elif isinstance(error_messages, dict):
                                error_message = error_messages.get("message", "")
                                error_key = error_messages.get("errorKey", "")
                            else:
                                error_message = "Unknown error"
                            print(f"{Fore.CYAN}Server response: {error_data}")
                            if "ticket purchase for this trip will be available" in error_message:
                                print(f"{Fore.YELLOW}Booking is not open yet: {error_message}. Retrying...")
                                await asyncio.sleep(MIN_LOOP_INTERVAL)
                                continue
                            if error_key == "OrderLimitExceeded":
                                print(f"{Fore.RED}Error: You have reached the maximum ticket booking limit for {train_booking_info['from_station']} to {train_booking_info['to_station']} on {train_booking_info['journey_date']}.")
                            else:
                                time_match = re.search(r"(\d+)\s*minute[s]?\s*(\d+)\s*second[s]?", error_message, re.IGNORECASE)
                                if time_match:
                                    minutes = int(time_match.group(1))
                                    seconds = int(time_match.group(2))
                                    total_seconds = minutes * 60 + seconds
                                    current_time_formatted = time.strftime("%I:%M:%S %p", time.localtime())
                                    future_time_formatted = time.strftime("%I:%M:%S %p", time.localtime(time.time() + total_seconds))
                                    print(f"{Fore.RED}Error: {error_message} Current system time is {current_time_formatted}. Try again after {future_time_formatted}.")
                                else:
                                    print(f"{Fore.YELLOW}{error_message} Please try again later.")
                            return None  
                        else:
                            print(f"{Fore.RED}Failed to fetch seat layout. HTTP: {response.status}")
                            text_resp = await response.text()
                            print(f"{Fore.CYAN}Server response: {text_resp}")
                except aiohttp.ClientError as e:
                    end_time = time.perf_counter()
                    elapsed = end_time - start_time
                    print(f"{Fore.RED}An error occurred while checking booking availability: {e}")
                if elapsed < MIN_LOOP_INTERVAL:
                    await asyncio.sleep(MIN_LOOP_INTERVAL - elapsed)
    def get_ticket_id(seat_layout,desired_seats,max_seat):




        selected_seats = {}
        if desired_seats:
            for coach in seat_layout:
                for row in coach['layout']:
                    for seat in row:
                        if(seat['seat_availability'] == 1 and seat['seat_number'] in desired_seats):
                            selected_seats[seat['ticket_id']] = seat['seat_number']
                            if(len(selected_seats)==max_seat):
                                return selected_seats
                    for coach in seat_layout:
                        for row in coach['layout']:
                            seat_numbers = [seat for seat in row if seat['seat_availability'] == 1]
                            for desired_seat in desired_seats:
                                nearby_seats = [s for s in seat_numbers if s['seat_number'] == desired_seat]
                                if nearby_seats:
                                    desired_index = seat_numbers.index(nearby_seats[0])
                                    for offset in range(1,len(seat_numbers)):
                                        if desired_index + offset < len(seat_numbers):
                                            seat = seat_numbers[desired_index + offset]
                                            if(seat['seat_availability']==1 and seat['seat_number'] not in selected_seats.values()):
                                                selected_seats[seat['ticket_id']] = seat['seat_number']
                                                if(len(selected_seats) == max_seat):
                                                    return selected_seats
                                        if desired_index - offset >=0:
                                            seat = seat_numbers[desired_index - offset]
                                            if seat['seat_availability'] == 1 and seat['seat_number'] not in selected_seats.values():
                                                selected_seats[seat['ticket_id']] = seat['seat_number']
                                                if(len(selected_seats)==max_seat):
                                                    return selected_seats
                    for coach in seat_layout:
                        for row in coach['layout']:
                            for seat in row:
                                if(seat['seat_availability'] == 1 and seat['seat_number'] not in selected_seats.values()):
                                    selected_seats[seat['ticket_id']] = seat['seat_number']
                                    if(len(selected_seats) == max_seat):
                                        return selected_seats
        else:
            selected_seats_list = []
            all_available_seats = []
            for layout in seat_layout:
                coach_name = layout['floor_name']
                seats = [seat for row in layout['layout'] for seat in row if seat['seat_availability']==1]
                if seats:
                    seats.sort(key = lambda x: int(x['seat_number'].split('-')[-1]))
                    all_available_seats.append({'coach': coach_name,'seats':seats})
            for coach_data in all_available_seats:
                coach_name = coach_data['coach']
                seats = coach_data['seats']
                mid_index = len(seats) //2
                for i in range(max(0,mid_index-max_seat),min(mid_index+1,len(seats) - max_seat+1)):
                    block = seats[i:i + max_seat]
                    seat_numbers = [int(seat['seat_number'].split('-')[-1]) for seat in block]
                    if max(seat_numbers) - min(seat_numbers) == max_seat - 1:
                        for seat in block:
                            selected_seats[seat['ticket_id']] = seat['seat_number']
                            if(len(selected_seats) >= max_seat):
                                return selected_seats
            for coach_data in all_available_seats:
                if(len(selected_seats_list) >= max_seat):
                    break
                coach_name = coach_data['coach']
                ets = coach_data['seats']
                coach_selected_seats = []
                mid_index = len(seats)//2
                left = mid_index-1
                right = mid_index
                while(len(selected_seats_list) < max_seat and (left>=0 or right <len(seats))):
                    if left >=0 and len(selected_seats_list) < max_seat:
                        coach_selected_seats.append(seats[left])
                        selected_seats_list.append(seats[left])
                        left -= 1
                    if right<len(seats) and len(selected_seats_list) < max_seat:
                        coach_selected_seats.append(seats[right])
                        selected_seats_list.append(seats[right])
                        right + 1
                if coach_selected_seats:
                    for seat in coach_selected_seats:
                        selected_seats[seat['ticket_id']] = seat['seat_number']
                        if(len(selected_seats) >= max_seat):
                            return selected_seats
            if(len(selected_seats) < max_seat):
                for coach_data in all_available_seats:
                    if(len(selected_seats_list) >= max_seat):
                        break
                    coach_name = coach_data['coach']
                    seats = coach_data['seats']
                    for seat in seats:
                        if len(selected_seats_list) >= max_seat:
                            break
                        if seat not in selected_seats.values():
                            selected_seats[seat['ticket_id']] = seat['seat_number']
                            selected_seats_list.append(seat)
                            if(len(selected_seats) >= max_seat):
                                return selected_seats
        if selected_seats:
            print(f"{Fore.YELLOW}Warning: Proceeding with {len(selected_seats)} instead of {max_seat}.")
            return selected_seats
        print(f"{Fore.RED} No seats available to proceed.")
        return None
  
  
  
  
  
  
  
  
    async def reserve_seat():
        global ticket_ids
        print(f"{Fore.YELLOW}Waiting for seat layout availability...")
        seat_layout = await is_booking_available()
        if not seat_layout:
            print(f"{Fore.RED}Seat layout could not be retrieved. Exiting.")
            return False
        ticket_id_map = get_ticket_id(seat_layout, train_booking_info['desired_seats'], train_booking_info['seat'])
        if not ticket_id_map:
            print(f"{Fore.RED}No matching seats found based on desired preferences. Exiting...")
            return False
        ticket_ids = list(ticket_id_map.keys())
        print(f"{Fore.GREEN}Seats matched Details: {', '.join([f'{ticket_id_map[ticket]} (Ticket ID: {ticket})' for ticket in ticket_ids])}")
        successful_ticket_ids = []
        stop_reservation_due_to_limit = False
        def reserve_single_seat(ticket):
            nonlocal stop_reservation_due_to_limit
            if stop_reservation_due_to_limit:
                return False
            url = "https://railspaapi.shohoz.com/v1.0/app/bookings/reserve-seat"
            payload = {
                "ticket_id": ticket,
                "route_id": route_id
            }
            while True:
                try:
                    response = requests.patch(url, headers=headers, json=payload)
                    print(f"{Fore.CYAN}Response from Reserve Seat API for seat {ticket_id_map[ticket]} (Ticket ID: {ticket}): {response.text}")
                    if response.status_code == 200:
                        data = response.json()
                        if data['data'].get("ack") == 1:
                            print(f"{Fore.GREEN}Seat {ticket_id_map[ticket]} (Ticket ID: {ticket}) reserved successfully.")
                            successful_ticket_ids.append(ticket)
                            return True
                        else:
                            print(f"{Fore.RED}Failed to reserve seat {ticket_id_map[ticket]} (Ticket ID: {ticket}): {data}")
                            return False
                    elif response.status_code == 422:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("messages", {}).get("error_msg", "")
                        if "Maximum 4 seats can be booked at a time" in error_msg:
                            print(f"{Fore.RED}Error: {error_msg}. Stopping further seat reservation.")
                            stop_reservation_due_to_limit = True
                            return False
                        elif "Sorry! this ticket is not available now." in error_msg:
                            print(f"{Fore.RED}Seat {ticket_id_map[ticket]} (Ticket ID: {ticket}) is not available now. Skipping retry...")
                            return False
                    elif response.status_code in [500, 502, 503, 504]:
                        print(f"{Fore.YELLOW}Server Overloaded (HTTP {response.status_code}). Retrying in 100 milliseconds...")
                        time.sleep(0.1)
                    else:
                        print(f"{Fore.RED}Error: {response.status_code} - {response.text}")
                        return False
                except Exception as e:
                    print(f"{Fore.RED}Exception occurred while reserving seat {ticket_id_map[ticket]} (Ticket ID: {ticket}): {e}")
                    time.sleep(0.1)
        print(f"{Fore.YELLOW}Initiating seat reservation process for {len(ticket_ids)} tickets...")

        
        # with ThreadPoolExecutor(max_workers=len(ticket_ids)) as executor:
        #     executor.map(reserve_single_seat, ticket_ids)

        for x in ticket_ids:
            reserve_single_seat(x)


        if successful_ticket_ids:
            ticket_ids = successful_ticket_ids
            print(f"{Fore.GREEN}Successfully reserved tickets {ticket_ids}. Proceeding to next step...")
            return True
        else:
            print(f"{Fore.RED}No seats could be reserved. Please try again...")
            return False
    def send_passenger_details():
        url = "https://railspaapi.shohoz.com/v1.0/app/bookings/passenger-details"
        payload = {
            "trip_id": trip_id,
            "trip_route_id": route_id,
            "ticket_ids": ticket_ids
        }
        while True:
            try:
                response = requests.post(url, headers=headers, json=payload)
                print(f"{Fore.CYAN}Response from Passenger Details API: {response.text}")
                if response.status_code == 200:
                    data = response.json()
                    if data["data"]["success"]:
                        print(f"{Fore.GREEN}OTP sent successfully!")
                        return True  
                    else:
                        print(f"{Fore.RED}Failed to send OTP: {data}")
                        return False  
                elif response.status_code in [500, 502, 503, 504]:
                    print(f"{Fore.YELLOW}Server Overloaded (HTTP {response.status_code}). Retrying in 1 second...")
                    time.sleep(1)  
                else:
                    print(f"{Fore.RED}Error: {response.status_code} - {response.text}")
                    return False  
            except requests.RequestException as e:
                print(f"{Fore.RED}Exception occurred while sending passenger details: {e}")
                time.sleep(1)  
    def send_passenger_details():
        url = "https://railspaapi.shohoz.com/v1.0/app/bookings/passenger-details"
        payload = {
            "trip_id": trip_id,
            "trip_route_id": route_id,
            "ticket_ids": ticket_ids
        }
        while True:
            try:
                response = requests.post(url, headers=headers, json=payload)
                print(f"{Fore.CYAN}Response from Passenger Details API: {response.text}")
                if response.status_code == 200:
                    data = response.json()
                    if data["data"]["success"]:
                        print(f"{Fore.GREEN}OTP sent successfully!")
                        return True  
                    else:
                        print(f"{Fore.RED}Failed to send OTP: {data}")
                        return False  
                elif response.status_code in [500, 502, 503, 504]:
                    print(f"{Fore.YELLOW}Server Overloaded (HTTP {response.status_code}). Retrying in 1 second...")
                    time.sleep(1)  
                else:
                    print(f"{Fore.RED}Error: {response.status_code} - {response.text}")
                    return False  
            except requests.RequestException as e:
                print(f"{Fore.RED}Exception occurred while sending passenger details: {e}")
                time.sleep(1)  
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
        verify_url = "https://railspaapi.shohoz.com/v1.0/app/bookings/verify-otp"
        verify_payload = {
            "trip_id": trip_id,
            "trip_route_id": route_id,
            "ticket_ids": ticket_ids,
            "otp": otp
        }
        try:
            while True:
                response = requests.post(verify_url, headers=headers, json=verify_payload)
                if response.status_code == 200:
                    data = response.json()
                    if not data["data"]["success"]:
                        print(f"{Fore.RED}Failed to verify OTP: {data}")
                        return False  
                    print(f"{Fore.GREEN}OTP verified Successfully!")
                    break  
                elif response.status_code in [500, 502, 503, 504]:
                    print(f"{Fore.YELLOW}Server overloaded (HTTP {response.status_code}). Retrying in 1 second...")
                    time.sleep(1)  
                elif response.status_code == 422:
                    data = response.json()
                    error_info = data.get("error", {}).get("messages", {})
                    error_message = error_info.get("message", "Unknown error")
                    error_key = error_info.get("errorKey", "Unknown errorkey")
                    print(f"{Fore.RED}Error: {error_message} (Error Key: {error_key})")
                    if error_key == "OtpNotVerified":
                        otp = input(f"{Fore.YELLOW}The OTP does not match. Please enter correct OTP: ")
                        verify_payload["otp"] = otp  
                    else:
                        print(f"{Fore.RED}Error: {response.status_code} - {response.text}")
                        return False  
        except Exception as e:
            print(f"{Fore.RED}Exception occurred: {e}")
            time.sleep(1)
            return False  
        confirm_url = "https://railspaapi.shohoz.com/v1.0/app/bookings/confirm"
        confirm_payload = prepare_confirm_payload(otp)
        print(f"\n{Fore.CYAN}Select Payment Method:")
        print(f"1. bKash\n2. Nagad\n3. Rocket\n4. Upay\n5. VISA\n6. Mastercard\n7. DBBL Nexus")
        while True:
            payment_choice = input(f"{Fore.YELLOW}Enter the number corresponding to your payment method: ")
            if payment_choice == '1':  
                print(f"{Fore.GREEN}Payment Method Selected: bKash")
                break
            elif payment_choice == '2':  
                confirm_payload["is_bkash_online"] = False
                confirm_payload["selected_mobile_transaction"] = 3
                print(f"{Fore.GREEN}Payment Method Selected: Nagad")
                break
            elif payment_choice == '3':  
                confirm_payload["is_bkash_online"] = False
                confirm_payload["selected_mobile_transaction"] = 4
                print(f"{Fore.GREEN}Payment Method Selected: Rocket")
                break
            elif payment_choice == '4':  
                confirm_payload["is_bkash_online"] = False
                confirm_payload["selected_mobile_transaction"] = 5
                print(f"{Fore.GREEN}Payment Method Selected: Upay")
                break
            elif payment_choice == '5':  
                confirm_payload["is_bkash_online"] = False
                confirm_payload.pop("selected_mobile_transaction", None)
                confirm_payload["pg"] = "visa"
                print(f"{Fore.GREEN}Payment Method Selected: VISA")
                break
            elif payment_choice == '6':  
                confirm_payload["is_bkash_online"] = False
                confirm_payload.pop("selected_mobile_transaction", None)
                confirm_payload["pg"] = "mastercard"
                print(f"{Fore.GREEN}Payment Method Selected: Mastercard")
                break
            elif payment_choice == '7':  
                confirm_payload["is_bkash_online"] = False
                confirm_payload.pop("selected_mobile_transaction", None)
                confirm_payload["pg"] = "nexus"
                print(f"{Fore.GREEN}Payment Method Selected: DBBL Nexus")
                break
            else:
                print(f"{Fore.RED}Invalid selection! Please enter a number between 1 and 7.")
        while True:
            response = requests.patch(confirm_url, headers=headers, json=confirm_payload)
            print(f"{Fore.CYAN}Response from Confirm Booking API: {response.text}")
            try:
                if response.status_code == 200:
                    data = response.json()
                    if "redirectUrl" in data["data"]:
                        redirect_url = data["data"]["redirectUrl"]
                        print(f"\n{Fore.GREEN}{'='*50}")
                        print(f"{Fore.GREEN}Booking confirmed successfully!")
                        print(f"{Fore.YELLOW}IMPORTANT: Please note that this payment link can be used ONLY ONCE.")
                        print(f"{Fore.BLUE}Payment URL: {redirect_url}")
                        webbrowser.open(redirect_url)
                        print(f"{Fore.GREEN}{'='*50}\n")
                        return True  
                    else:
                        print(f"{Fore.RED}Failed to confirm booking: {data}")
                        return False  
                elif response.status_code in [500, 502, 503, 504]:
                    print(f"{Fore.YELLOW}Server overloaded (HTTP {response.status_code}). Retrying in 1 second...")
                    time.sleep(1)  
                else:
                    print(f"{Fore.RED}Error: {response.status_code} - {response.text}")
                    return False  
            except requests.RequestException as e:
                print(f"{Fore.RED}Exception occurred while confirming booking: {e}")
                time.sleep(1)
                return False  
    try:
        if not token:
            print(f"{Fore.RED}Failed to fetch auth token. Exiting...")
            sys.exit(1)
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
        if  asyncio.run(reserve_seat()):  
            if send_passenger_details():
                print(f"{Fore.CYAN}Proceeding to OTP verification and confirmation...")
                otp = input(f"{Fore.YELLOW}Enter OTP received: ")
                if verify_and_confirm(otp):
                    print(f"{Fore.GREEN}Booking Process completed Successfully!")
                    return True
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
def countdown():
    from datetime import datetime, time as dt_time
    target_time = dt_time(7, 59, 30)
    def is_before_target_time():
        current_time = datetime.now().time()
        return current_time < target_time
    while is_before_target_time():
        os.system('cls' if os.name == 'nt' else 'clear')  
        current_time = datetime.now().time()
        time_left = datetime.combine(datetime.today(), target_time) - datetime.combine(datetime.today(), current_time)
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"Time left: {hours:02}:{minutes:02}:{seconds:02}\nCurrent Time :{datetime.now().strftime("%I:%M:%S %p")}")
        time.sleep(1)
# countdown()
while True:
    os.system('cls' if os.name == 'nt' else 'clear')
    if(main()):
        break
