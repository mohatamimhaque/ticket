document.getElementById("myForm").addEventListener("submit", function(event) {
    event.preventDefault();
    let formData = new FormData(this);  // Get form data

    let formObject = {};
    formData.forEach((value, key) => {
        formObject[key] = value;
    });
    const paymentMethods = [
        "bKash", "Nagad", "Rocket", "Upay", "VISA", "Mastercard", "DBBL Nexus"
    ];

    const phone_number = formObject['floating_phone'];
    const password = formObject['floating_password'];
    const origin = formObject['origin_station'];
    const destination = formObject['destination_station'];
    const journey_date = getTodayFormatted(formObject['journey_date']);
    const match = formObject['select_train'].match(/\((\d+)\)/);
    const train_number = match ? match[1] : null;
    const seat_class = formObject['seat_class'];
    const max_seat = parseInt(formObject['max_seat']);
    const payment_method = paymentMethods.indexOf(formObject['payment_method'])+1;
    const desired_seats = formObject['desired_seat'].split(',');
    const time = formObject['time'];
    const p_names = []
    const p_types = []
    const p_gender = []
    const message_box = document.querySelector('.message_box');

    if(max_seat>1){
        for (let i = 2; i <= max_seat; i++) {
            p_names.push(formObject[`p_name${i}`]);
            p_types.push(formObject[`p_type${i}`]);
            p_gender.push(formObject[`p_gender${i}`]);
        }
    }


    
    
    function getTodayFormatted(date) {
        const today = new Date(date);
        
        const day = today.getDate();
        const month = today.toLocaleString('default', { month: 'short' }); // e.g., "Mar"
        const year = today.getFullYear();
        
        const formattedDate = `${day}-${month}-${year}`;
        
        return formattedDate;
    }




    const [hours, minutes, seconds] = time.split(':').map(Number);
    const targetTime = new Date();
    targetTime.setHours(hours, minutes, seconds, 0);

    const countdownInterval = setInterval(updateCountdown, 1000, targetTime);

    function updateCountdown(targetTime) {
        const now = new Date().getTime();
        const timeDifference = targetTime - now;
        
        if (timeDifference <= 0) {
            clearInterval(countdownInterval);
            message_box.innerHTML = "";
            while(true){
                if(train_booking()){
                    break;
                }

            }
            return;
        }
        
        const hours = Math.floor((timeDifference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeDifference % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeDifference % (1000 * 60)) / 1000);
        
        const countdownElement = `${hours}:${minutes}:${seconds}`;
        message_box.innerHTML = `<p class="mb-2 text-xl tracking-tight text-gray-200 dark:text-gray-500">Wait...</p>
                        <h3 class="mb-2 text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-900 text-center countdown">${countdownElement}</h3>`
    }

    updateCountdown(targetTime);




    function showMessage(message, type) {
        if (message_box) {
            message_box.innerHTML = `<p class="p-2 rounded-md text-white ${
                type === "success" ? "bg-green-500" : type === "warning" ? "bg-yellow-500" : "bg-red-500"
            }">${message}</p>`;
        }
    }

    

    //token generator
    function authToken(phone_number, password, max_retries = 50) {
        const url = "https://railspaapi.shohoz.com/v1.0/app/auth/sign-in";
        const payload = {
          mobile_number: phone_number,
          password: password,
        };
      
        let retries = 0;
      
        function makeRequest() {
          return fetch(url, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
          })
            .then((response) => {
              if (response.ok) {
                return response.json().then((data) => {
                  const token = data?.data?.token;
                  if (token) {
                    showMessage("Success: Auth Token retrieved.", "text-green-600");
                    return token;
                  } else {
                    showMessage("Failed to retrieve auth token from response.", "text-red-600");
                    throw new Error("No token found in response");
                  }
                });
              } else if ([500, 502, 503, 504].includes(response.status)) {
                showMessage(`Server error ${response.status}. Retrying in 1 second... (${retries + 1}/${max_retries})`, "text-yellow-600");
                throw new Error("Server error");
              } else {
                return response.text().then((text) => {
                  showMessage(`Error: ${response.status} - ${text}`, "text-red-600");
                  throw new Error(`HTTP error: ${response.status}`);
                });
              }
            })
            .catch((error) => {
              if (retries < max_retries) {
                retries++;
                return new Promise((resolve) => setTimeout(resolve, 1000)).then(makeRequest);
              } else {
                showMessage("Max retries reached. Failed to obtain auth token.", "text-red-600");
                throw error;
              }
            });
        }
      
        return makeRequest();
      }
      
      function showMessage(message, colorClass) {
        const messageBox = document.getElementById("message_box");
        const p = document.createElement("p");
        p.className = `${colorClass} text-sm`;
        p.textContent = message;
        messageBox.appendChild(p);
      }
      
   
      authToken(phone_number, password)
        .then((token) => {
          if (token) {
            const headers = { Authorization: `Bearer ${token}` };
            showMessage(`Token: ${token}`, "text-green-600");
            showMessage(`Headers: ${JSON.stringify(headers)}`, "text-green-600");
          }
        })
        .catch((error) => {
          console.error("Failed to get auth token:", error);
        });





    function train_booking(){



        return true;
    }

    
    
    
    
    
    
    
    
        console.log(time);
        console.log(phone_number,password,origin,destination,journey_date,seat_class,max_seat,payment_method,desired_seats,train_number,p_names,p_types,p_gender);
    

});