let form = document.getElementById('form');
let button = document.getElementById('submitButton');
let spinner = document.getElementById('spinner'); 
let buttonText = document.getElementById('buttonText');
let messageDiv = document.getElementById('messages');
let responseDiv = document.getElementById('response');

const classHidden = 'visually-hidden';
const alertCloseButton = '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
const dtParams = {
    pageLength: 25,
    order: [[2, 'desc']],
};

function describe(msg) {
    switch (msg.category) {
        case 'PaperNotFoundWarning':
            return `Failed to find the following paper: <tt>${msg.message}</tt>`;

        case 'EmptyGroupError':
            return `Group <tt>${msg.message}</tt> is empty`;

        default:
            console.log(`Unexpected warning/error: ${msg.category}/${msg.message}`);
            break;
    }
}

function buttonReady() {
    button.disabled = false;
    spinner.classList.add(classHidden);
    buttonText.innerText = 'Submit';
}

function buttonBusy() {
    button.disabled = true;
    spinner.classList.remove(classHidden);
    buttonText.innerText = 'Waiting for response...'
}

function constructMessageDiv(type, msg) {
    var div = document.createElement("div");
    div.setAttribute('role', 'alert');
    div.classList.add('alert');
    switch (type) {
        case 'error':
            div.classList.add("alert-danger");            
            div.innerHTML = `<strong>Error!</strong>&nbsp;<span>${describe(msg)}</span>\n${alertCloseButton}`;
            break;

        case 'warning':
            div.classList.add("alert-warning");
            div.innerHTML = `<strong>Warning!</strong>&nbsp;<span>${describe(msg)}</span>\n${alertCloseButton}`;
            break;

        default:
            console.log(`Unexpected alert type: ${type}`);
            break;
    }

    div.classList.add('alert-dismissible', 'fade', 'show');

    return div;
}

function appendMessage(type, message) {
    messageDiv.classList.remove(classHidden);
    messageDiv.append(constructMessageDiv(type, message));
}

function cleanMessages() {
    messageDiv.replaceChildren();
}

function submitForm(event) {
    // Disable the button
    buttonBusy();

    // Clean the error log
    cleanMessages();

    // Validation
    isValid = form.checkValidity();
    form.classList.add('was-validated');
    if (!isValid) {
        event.preventDefault();
        event.stopPropagation();
        buttonReady();
        return;
    }

    // Fetch & wait for response
    event.preventDefault();
    const formData = new FormData(event.target);
    // fetch('https://crosscheck.herokuapp.com/api/crosscheck', {
    fetch('http://crosscheck.app/api/crosscheck', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if ((response.ok) || (response.status == 400)) {
            console.log('Parsing JSON');
            return response.json();
        } else {
            throw Error('Internal server error');
        }
    })
    .then(response => {
        console.log(response);
    
        // Display warnings
        response.messages.forEach(m => {
            appendMessage('warning', m);
        });
    
        // Display error if present
        if ("error" in response) {
            let e = response['error'];
            appendMessage('error', e);
        }

        // Display data if present
        if ("data" in response) {
            responseDiv.innerHTML = response.data;
            $('#dataTable').DataTable( dtParams );
        }
    
        // Enable button
        buttonReady();
    })
    .catch((error) => {
        console.log(error);
    
        appendMessage('error', 'Failed due to a network error');
    
        // Enable button
        buttonReady();
    });
}

form.addEventListener('submit', submitForm);