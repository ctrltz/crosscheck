const classHidden = 'visually-hidden';
const alertCloseButton = '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
const searchHistorySize = 25;

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
    // Initialize the table with DataTables
    return $('#historyTable').DataTable({
        // Use the array of objects as the data source for the table
        "data": [],
        // Add a checkbox column to the table
        "columnDefs": [{
                "targets": 0,
                "checkboxes": {
                    "selectRow": true
                }
            },
            // hide the last column that contains URL of the paper
            {
                "targets": 4,
                visible: false,
            }
        ],
        "columns": [
            { "data": null },
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
        // Display the table with the 'select' extension
        "select": {
            "style": "multi"
        },
        // Other options and settings
        "paging": false,
        "pageLength": searchHistorySize,
        "language": {
            "emptyTable": "No data is available in the table"
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
    let button = document.getElementById('submitButton');
    let spinner = document.getElementById('spinner'); 
    let buttonText = document.getElementById('buttonText');
    let messageDiv = document.getElementById('messages');

    // Retrieve the object from local storage
    let papers = JSON.parse(localStorage.getItem('papers'));

    // Use an empty array as the default value
    papers = papers || [];
    console.log({papers});

    // Initialize the results table
    let resultsTable = initResultsTable();

    // Initialize the search history table
    let historyTable = initSearchHistoryTable();
    if (papers.length > 0) {
        historyTable.rows.add(papers)
                    .columns.adjust()
                    .draw();
    }

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
        resultsTable.clear().draw();
    
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

    // Handle clicks on the 'Add to Group 1' button
    $('#addToGroup1Btn').click(handleSelectedPapers(historyTable, '#floatingTextArea'));

    // Handle clicks on the 'Add to Group 2' button
    $('#addToGroup2Btn').click(handleSelectedPapers(historyTable, '#floatingTextArea2'));
});