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

// Function to handle the selected papers
function handleSelectedPapers(table, textareaId) {
    // Get the selected rows
    var rows = table.rows({ selected: true }).data();
  
    // Extract the paperIds of the selected papers
    var paperIds = rows.map(function(row) {
      return row[4]; // The paperId is in the fifth column of the table
    });
  
    // Append the paperIds to the textarea
    $(textareaId).val(function(i, val) {
      return val + paperIds.join('\n') + '\n';
    });
}

function initSearchHistoryTable() {
    // Retrieve the object from local storage
    let papers = JSON.parse(localStorage.getItem('papers'));

    // Use an empty array as the default value
    papers = papers || [];

    // Convert the object to an array of objects
    let data = Object.keys(papers).map(function(key) {
        return {
            title: papers[key].title,
            year: papers[key].year,
            citationCount: papers[key].citationCount,
            paperId: papers[key].paperId
        };
    });

    // Initialize the table with DataTables
    let table = $('#papersTable').DataTable({
        // Use the array of objects as the data source for the table
        "data": data,
        // Add a checkbox column to the table
        "columnDefs": [{
            "targets": 0,
            "checkboxes": {
                "selectRow": true
            }
        }, {
            // Make the paperId column hidden
            "targets": 4,
            "className": "d-none"
        }],
        // Display the table with the 'select' extension
        "select": {
            "style": "multi"
        },
        // Other options and settings
        "paging": false,
        "ordering": false,
        "info": false
    });

    return table;
}

$(document).ready(function() {
    let form = document.getElementById('form');
    let button = document.getElementById('submitButton');
    let spinner = document.getElementById('spinner'); 
    let buttonText = document.getElementById('buttonText');
    let messageDiv = document.getElementById('messages');
    let responseDiv = document.getElementById('response');

    // Enable submit
    function buttonReady() {
        button.disabled = false;
        spinner.classList.add(classHidden);
        buttonText.innerText = 'Submit';
    }
    
    // Disable submit
    function buttonBusy() {
        button.disabled = true;
        spinner.classList.remove(classHidden);
        buttonText.innerText = 'Waiting for response...'
    }

    // Add message
    function appendMessage(type, message) {
        messageDiv.classList.remove(classHidden);
        messageDiv.append(constructMessageDiv(type, message));
    }

    // Display the results, warning, and errors for the submitted form
    function submitForm(event) {
        // Disable the button
        buttonBusy();
    
        // Clear the error log
        messageDiv.replaceChildren();
    
        // Clear the results
        responseDiv.replaceChildren();
    
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

    // Attach action to the submit button
    form.addEventListener('submit', submitForm);

    // Initialize the search history
    let table = initSearchHistoryTable();

    // Handle clicks on the 'Add to Group 1' button
    $('#addToGroup1Btn').click(handleSelectedPapers(table, '#floatingTextArea'));

    // Handle clicks on the 'Add to Group 2' button
    $('#addToGroup2Btn').click(handleSelectedPapers(table, '#floatingTextArea2'));
});