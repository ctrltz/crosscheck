// TODO: get rid of jquery?

const classHidden = 'visually-hidden';
const alertCloseButton = '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
const searchHistorySize = 25;
const urlColumn = 3;
const serverURL = 'https://crosscheck.herokuapp.com/api/crosscheck';
// const serverURL = 'http://crosscheck.app/api/crosscheck';

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

function initSearchHistoryTable() {
    // Initialize the table with DataTables
    return $('#historyTable').DataTable({
        // Use the array of objects as the data source for the table
        "data": [],
        // Add a checkbox column to the table
        "columnDefs": [
            // hide the last column that contains URL of the paper
            {
                "targets": urlColumn,
                visible: false,
            }
        ],
        "columns": [
            {
                // The 'Title' column displays the title, authors, and journal in separate elements
                "data": "title",
                "render": function(data, type, row) {
                    var authors = row.authors ? `<br/><small class="text-secondary">${row.authors}</small>` : "";
                    var journal = row.journal ? `&nbsp;<small class="text-secondary">&#8226;</small>&nbsp;<small class="text-secondary">${row.journal}</small>` : "";
                    return `<a href="${row.url}" class="text-reset" target=”_blank”>${row.title}</a>${authors}${journal}`;
                }
            },
            { "data": "year" },
            { "data": "citationCount" },
            { "data": "url" }
        ],
        // Other options and settings
        "paging": false,
        "pageLength": searchHistorySize,
        "order": [[0, 'asc']],
        "language": {
            "emptyTable": "Search history is empty"
        }
    });
}

function initResultsTable() {
    // Initialize the table with DataTables
    return $('#dataTable').DataTable({
        // Use the array of objects as the data source for the table
        "data": [],
        // Define the columns of the table
        "columns": [
            {
                // The 'Title' column displays the title, authors, and journal in separate elements
                "data": "title",
                "render": function(data, type, row) {
                    var authors = row.authors ? `<br/><small class="text-secondary">${row.authors}</small>` : "";
                    var journal = row.journal ? `&nbsp;<small class="text-secondary">&#8226;</small>&nbsp;<small class="text-secondary">${row.journal}</small>` : "";
                    return `<a href="${row.url}" class="text-reset" target=”_blank”>${row.title}</a>${authors}${journal}`;
                }
            },
            { "data": "year" },
            { "data": "citationCount" },
        ],
        // Other options and settings
        "pageLength": 25,
        "order": [[2, 'desc']],
        "language": {
            "emptyTable": "No data is available in the table"
        }
    });
}

function updateHistory(papers, new_papers) {
    // TODO: deal with repetitions

    // Add new papers
    papers.push(...new_papers);

    // Remove the oldest papers
    while (papers.length > 25) {
        papers.pop();
    }

    return papers;
}

$(document).ready(function() {
    let form = document.getElementById('form');
    let submitButton = document.getElementById('submitButton');
    let addGroup1Button = document.getElementById('addToGroup1Btn');
    let addGroup2Button = document.getElementById('addToGroup2Btn');
    let group1Textarea = document.getElementById('group1Textarea');
    let group2Textarea = document.getElementById('group2Textarea');
    let spinner = document.getElementById('spinner'); 
    let buttonText = document.getElementById('buttonText');
    let messageDiv = document.getElementById('messages');

    // Enable tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // Retrieve the object from local storage
    let papers = JSON.parse(localStorage.getItem('papers'));

    // Use an empty array as the default value
    papers = papers || [];

    // Initialize the results table
    let resultsTable = initResultsTable();

    // Initialize the search history table
    let historyTable = initSearchHistoryTable();
    if (papers.length > 0) {
        historyTable.rows.add(papers)
                    .columns.adjust()
                    .draw();
    }

    // Enable select on rows of history table
    $('#historyTable tbody').on('click', 'tr', function () {
        $(this).toggleClass('selected');

        // Enable add button if some papers are selected
        let countSelected = historyTable.rows('.selected').data().length;
        if (countSelected > 0) {
            addGroup1Button.disabled = false;
            addGroup2Button.disabled = false;
        } else {
            addGroup1Button.disabled = true;
            addGroup2Button.disabled = true;
        }
    });

    // Function to handle the selected papers
    function handleSelectedPapers(textarea) {
        // Get the selected rows
        let rows = historyTable.rows('.selected').data();
        let urls = rows.map((row) => row.url);

        // Append the urls to the textarea if not empty
        textarea.value = textarea.value + '\n' + urls.join('\n');

        // Reset the selection
        historyTable.rows('.selected').every( function () {
            this.node().classList.remove('selected');
        } );
    }

    // Enable submit
    function submitButtonReady() {
        submitButton.disabled = false;
        spinner.classList.add(classHidden);
        buttonText.innerText = 'Submit';
    }
    
    // Disable submit
    function submitButtonBusy() {
        submitButton.disabled = true;
        spinner.classList.remove(classHidden);
        buttonText.innerText = 'Waiting for response...'
    }

    // Add message
    function appendMessage(type, message) {
        messageDiv.classList.remove(classHidden);
        messageDiv.append(constructMessageDiv(type, message));
    }

    // Display the results
    function displayResults(response) {
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
            resultsTable.rows.add(response.data)
                        .columns.adjust()
                        .draw();
        }

        // Update search history
        if ("source" in response) {
            console.log('Before:', papers, response.source);
            papers = updateHistory(papers, response.source);
            console.log('After:', papers);
            localStorage.setItem('papers', JSON.stringify(papers));
            historyTable.clear()
                        .rows.add(papers)
                        .columns.adjust()
                        .draw();
        }
    
        // Enable button
        submitButtonReady();
    }

    // Retrieve the results
    function retrieveResults(taskID) {
        fetch(`${serverURL}/${taskID}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
        })
        .then(response => response.json())
        .then(response => {      
            const taskStatus = response.task_status;
            if (taskStatus === 'SUCCESS' || taskStatus === 'FAILURE') {
                return displayResults(response.task_result);
            }
            setTimeout(function() {
                retrieveResults(response.task_id);
            }, 1000);
        })
        .catch((error) => {       
            appendMessage('error', 'Failed due to a network error');
        
            // Enable button
            submitButtonReady();
        });
    }

    // Display the results, warning, and errors for the submitted form
    function submitForm(event) {
        // Disable the button
        submitButtonBusy();
    
        // Clear the error log
        messageDiv.replaceChildren();
    
        // Clear the results
        resultsTable.clear().draw();
    
        // Validation
        isValid = form.checkValidity();
        form.classList.add('was-validated');
        if (!isValid) {
            event.preventDefault();
            event.stopPropagation();
            submitButtonReady();
            return;
        }
    
        // Fetch & wait for response
        event.preventDefault();
        const formData = new FormData(event.target);
        fetch(serverURL, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => retrieveResults(data.task_id))
        .catch((error) => {      
            appendMessage('error', 'Failed due to a network error');
        
            // Enable button
            submitButtonReady();
        });
    }

    // Attach action to the submit button
    form.addEventListener('submit', submitForm);

    // Handle clicks on the 'Add to Group 1/2' buttons
    addGroup1Button.addEventListener('click', function(e) {
        handleSelectedPapers(group1Textarea);
    });
    addGroup2Button.addEventListener('click', function(e) {
        handleSelectedPapers(group2Textarea);
    });
});