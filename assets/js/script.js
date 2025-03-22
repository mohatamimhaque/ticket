function togglePasswordVisibility(passwordFieldId, eyeIconId) {
    const passwordInput = document.getElementById(passwordFieldId);
    const eyeIcon = document.getElementById(eyeIconId);

    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        eyeIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.97 10.97 0 0112 19c-7 0-9.5-7-9.5-7s2.5-7 9.5-7a10.97 10.97 0 011.875.175"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12c-2-5-5.5-8-9-8s-7 3-9 8c2 5 5.5 8 9 8s7-3 9-8z"/>';
    } else {
        passwordInput.type = "password";
        eyeIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.5 12a3.5 3.5 0 11-7 0 3.5 3.5 0 017 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.5 12S5 5 12 5s9.5 7 9.5 7-2.5 7-9.5 7S2.5 12 2.5 12z"/>';
    }
}

document.getElementById("togglePassword").addEventListener("click", function() {
    togglePasswordVisibility("floating_password", "eyeIcon");
});





const inputOrigin = document.getElementById('origin_station');
const dropdownOrigin = document.getElementById('dropdownList');

const inputDestination = document.getElementById('destination_station');
const dropdownDestination = document.getElementById('dropdownList2');

let stations = [];

fetch('station.json')
    .then(response => response.json())
    .then(data => {
        stations = data.stations;
    })
    .catch(error => console.error('Error loading JSON:', error));

function setupStation(inputBox, dropdownList) {
    inputBox.addEventListener('focus', function() {
        if (inputBox.value.length === 0 || inputBox.value === '') {
            dropdownList.innerHTML = '';
            show(stations);
        }
    })
    inputBox.addEventListener('input', function() {
        const query = inputBox.value.toLowerCase();
        dropdownList.innerHTML = '';

        if (query) {
            const filteredStations = stations.filter(station => station.toLowerCase().includes(query));
            if (filteredStations.length > 0) {
                show(filteredStations);
            } else {
                dropdownList.style.display = 'none';
            }
        } else {
            dropdownList.style.display = 'none';
        }
    });

    function show(filteredStations) {
        dropdownList.style.display = 'block';
        filteredStations.forEach(station => {
            const li = document.createElement('li');
            li.classList.add('block', 'px-4', 'py-2', 'hover:bg-gray-100', 'dark:hover:bg-gray-600', 'dark:hover:text-white');
            li.textContent = station;
            li.addEventListener('click', function() {
                inputBox.value = station;
                dropdownList.style.display = 'none';
            });
            dropdownList.appendChild(li);
        });
    }


    document.addEventListener('click', function(event) {
        if (!inputBox.contains(event.target) && !dropdownList.contains(event.target)) {
            dropdownList.style.display = 'none';
        }
    });
}

setupStation(inputOrigin, dropdownOrigin);
setupStation(inputDestination, dropdownDestination);

function setupTrain(inputBox, dropdownList) {
    let trains = {};

    fetch('train.json')
        .then(response => response.json())
        .then(data => {
            trains = data; // Store the fetched data in the trains object
        })
        .catch(error => console.error('Error loading train data:', error));

    inputBox.addEventListener('focus', function() {
        if (inputBox.value.length === 0 || inputBox.value === '') {
            dropdownList.innerHTML = '';
            show(Object.entries(trains));
        }
    })
    inputBox.addEventListener('input', function() {
        const query = inputBox.value.toLowerCase();
        dropdownList.innerHTML = '';

        if (query) {
            const filteredTrains = Object.entries(trains).filter(([code, name]) =>
                name.toLowerCase().includes(query) || code.includes(query)
            );

            if (filteredTrains.length > 0) {
                show(filteredTrains);
            } else {
                dropdownList.style.display = 'none';
            }
        } else {
            dropdownList.style.display = 'none';
        }
    });

    function show(filteredTrains) {
        dropdownList.style.display = 'block';
        filteredTrains.forEach(([code, name]) => {
            const li = document.createElement('li');
            li.classList.add('block', 'px-4', 'py-2', 'hover:bg-gray-100', 'dark:hover:bg-gray-600', 'dark:hover:text-white');
            li.textContent = `${name} (${code})`;
            li.addEventListener('click', function() {
                inputBox.value = `${name} (${code})`;
                dropdownList.style.display = 'none';
            });
            dropdownList.appendChild(li);
        });
    }


    document.addEventListener('click', function(event) {
        if (!inputBox.contains(event.target) && !dropdownList.contains(event.target)) {
            dropdownList.style.display = 'none';
        }
    });
}

setupTrain(document.getElementById('select_train'), document.getElementById('dropdownList3'))




function seat_class(inputBox, dropdownList) {
    const seatTypes = [
        "AC_B", "AC_S", "SNIGDHA", "F_BERTH", "F_SEAT", "F_CHAIR", "S_CHAIR", "SHOVAN", "SHULOV", "AC_CHAIR"
    ];

    inputBox.addEventListener('focus', function() {
        if (inputBox.value.length === 0 || inputBox.value === '') {

            dropdownList.style.display = 'block';
            dropdownList.innerHTML = '';
            show(seatTypes);
        }
    })
    inputBox.addEventListener('input', function() {
        const query = inputBox.value.trim().toUpperCase();
        dropdownList.innerHTML = '';

        if (query) {
            const filteredSeatTypes = seatTypes.filter(seatType =>
                seatType.includes(query)
            );

            if (filteredSeatTypes.length > 0) {
                dropdownList.style.display = 'block';
                show(filteredSeatTypes);
            } else {
                dropdownList.style.display = 'none';
            }
        } else {
            dropdownList.style.display = 'none';
        }
    });

    function show(filteredSeatTypes) {
        filteredSeatTypes.forEach(seatType => {
            const li = document.createElement('li');
            li.classList.add('block', 'px-4', 'py-2', 'hover:bg-gray-100', 'dark:hover:bg-gray-600', 'dark:hover:text-white');
            li.textContent = seatType;
            li.addEventListener('click', function() {
                inputBox.value = seatType;
                dropdownList.style.display = 'none';
            });
            dropdownList.appendChild(li);
        });
    }

    document.addEventListener('click', function(event) {
        if (!inputBox.contains(event.target) && !dropdownList.contains(event.target)) {
            dropdownList.style.display = 'none';
        }
    });
}

seat_class(document.getElementById('seat_class'), document.getElementById('dropdownList4'))




function max_seat(inputBox, dropdownList) {
    const seatTypes = [
        "1", "2", "3", "4"
    ];

    inputBox.addEventListener('focus', function() {
        if (inputBox.value.length === 0 || inputBox.value === '') {

            dropdownList.innerHTML = '';
            show(seatTypes);
        }
    })
    inputBox.addEventListener('input', function() {
        const query = inputBox.value.trim().toUpperCase();
        dropdownList.innerHTML = '';

        if (query) {
            const filteredSeatTypes = seatTypes.filter(seatType =>
                seatType.includes(query)
            );

            if (filteredSeatTypes.length > 0) {
                show(filteredSeatTypes)
            } else {
                dropdownList.style.display = 'none';
            }
        } else {
            dropdownList.style.display = 'none';
        }
    });

    function show(filteredSeatTypes) {
        dropdownList.style.display = 'block';
        filteredSeatTypes.forEach(seatType => {
            const li = document.createElement('li');
            li.classList.add('block', 'px-4', 'py-2', 'hover:bg-gray-100', 'dark:hover:bg-gray-600', 'dark:hover:text-white');
            li.textContent = seatType;
            li.addEventListener('click', function() {
                inputBox.value = seatType;
                dropdownList.style.display = 'none';

                let event = new Event("input", {
                    bubbles: true
                });
                document.getElementById('max_seat').dispatchEvent(event);
            });
            dropdownList.appendChild(li);
        });
    }

    document.addEventListener('click', function(event) {
        if (!inputBox.contains(event.target) && !dropdownList.contains(event.target)) {
            dropdownList.style.display = 'none';
        }
    });
}

max_seat(document.getElementById('max_seat'), document.getElementById('dropdownList5'))




const maxSeatInput = document.getElementById('max_seat');
const submitButton = document.getElementById('submit');
const additional_passenger = document.getElementById('additional_passenger');
const phoneInput = document.getElementById('floating_phone');
const phoneError = document.getElementById('phone-error');

phoneInput.addEventListener('input', function() {
    const phoneNumber = phoneInput.value.trim();

    if (isValidBangladeshPhoneNumber(phoneNumber)) {
        phoneError.style.display = 'none';
        phoneInput.setCustomValidity('');
    } else {
        phoneError.style.display = 'block';
        phoneInput.setCustomValidity('Invalid phone number');
    }
});

function isValidBangladeshPhoneNumber(phoneNumber) {
    const regex = /^(?:\+88)?01[3-9]\d{8}$/;
    return regex.test(phoneNumber);
}
maxSeatInput.addEventListener('input', function() {
    const value = parseInt(maxSeatInput.value, 10); // Convert input value to integer
    let isValid = true;
    if (isNaN(value) || value === 0 || value > 4) {
        isValid = false;
        additional_passenger.style.display = 'none';
        additional_passenger.innerHTML = "";
    } else if (value == 1) {
        additional_passenger.style.display = 'none';
        additional_passenger.innerHTML = "";
    } else {
        additional_passenger.style.display = 'block';
        additional_passenger.innerHTML = `<h5 class="text-base text-gray-500 dark:text-gray-200">Extra passenger details:</details></h5>`;
        for (let i = 2; i <= value; i++) {
            additional_passenger.innerHTML += `
                <h6 class="text-sm text-gray-500 dark:text-gray-200">Passenger ${i}:</details></h6>
                <div class="grid md:grid-cols-3 md:gap-4 mx-auto" style="z-index: 2;">
                    <div class="relative z-0 w-full mb-5 group">
                        <input type="text" value="xxxx" name="p_name${i}" id="p_name${i}" class="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none dark:text-white dark:border-gray-600 dark:focus:border-blue-500 focus:outline-none focus:ring-0 focus:border-blue-600 peer" placeholder="Name" required />
                    </div>
                    <div class="relative z-0 w-full mb-5 group" >
                        <label for="p_type"  class="sr-only">Passenger Type</label>
                        <select id="p_type${i}" name="p_type${i}" class="block py-2.5 px-0 w-full text-sm text-gray-500 bg-transparent border-0 border-b-2 border-gray-200 appearance-none dark:text-gray-400 dark:border-gray-700 focus:outline-none focus:ring-0 focus:border-gray-200 peer">
                            <option value="Adult" selected>Adult</option>
                            <option value="Child">Child</option>
                        </select> 
                    </div>
                    <div class="relative z-0 w-full mb-5 group" >
                        <label for="p_gender${i}"  class="sr-only">Gender</label>
                        <select id="p_gender${i}" name="p_gender${i}" class="block py-2.5 px-0 w-full text-sm text-gray-500 bg-transparent border-0 border-b-2 border-gray-200 appearance-none dark:text-gray-400 dark:border-gray-700 focus:outline-none focus:ring-0 focus:border-gray-200 peer">
                            <option value="Male" selected>Male</option>
                            <option value="Female">Female</option>
                        </select> 
                    </div>
                </div>
            
            `
        }
    }

    submitButton.disabled = !isValid;
});




function payment_method(inputBox, dropdownList) {
    const paymentMethods = [
        "bKash", "Nagad", "Rocket", "Upay", "VISA", "Mastercard", "DBBL Nexus"
    ];

    inputBox.addEventListener('focus', function() {
        if (inputBox.value.length === 0 || inputBox.value === '') {
            dropdownList.innerHTML = '';
            show(paymentMethods); // Show all payment methods when input is empty and focused
        }
    });

    inputBox.addEventListener('input', function() {
        const query = inputBox.value.trim().toLowerCase(); 
        dropdownList.innerHTML = '';

        if (query) {
            const filteredPaymentMethods = paymentMethods.filter(method =>
                method.toLowerCase().includes(query) 
            );

            if (filteredPaymentMethods.length > 0) {
                show(filteredPaymentMethods);
                dropdownList.style.display = 'none'; 
            }
        } else {
            dropdownList.style.display = 'none'; 
        }
    });

    function show(filteredPaymentMethods) {
        dropdownList.style.display = 'block'; 
        filteredPaymentMethods.forEach(method => {
            const li = document.createElement('li');
            li.classList.add('block', 'px-4', 'py-2', 'hover:bg-gray-100', 'dark:hover:bg-gray-600', 'dark:hover:text-white');
            li.textContent = method;
            li.addEventListener('click', function() {
                inputBox.value = method; 
                dropdownList.style.display = 'none'; 

                let event = new Event("input", {
                    bubbles: true
                });
                inputBox.dispatchEvent(event);
            });
            dropdownList.appendChild(li);
        });
    }

    document.addEventListener('click', function(event) {
        if (!inputBox.contains(event.target) && !dropdownList.contains(event.target)) {
            dropdownList.style.display = 'none';
        }
    });
}

payment_method(document.getElementById('payment_method'), document.getElementById('dropdownList6'))




document.getElementById("myForm").addEventListener("submit", function(event) {
    event.preventDefault();
});