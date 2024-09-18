// web/static/js/main.js

async function fetchData(endpoint) {
    const response = await fetch(endpoint);
    const data = await response.json();
    alert(data.message);

    // Track reload button click
    gtag('event', 'click', {
        'event_category': 'Button',
        'event_label': endpoint.includes('config') ? 'Reload Config' : 'Reload Data'
    });
}

async function loadResponseTypes() {
    const response = await fetch('/api/response-types');
    const data = await response.json();
    const responseTypeContainer = document.getElementById('responseTypeOptions');
    responseTypeContainer.innerHTML = ''; // Clear existing options

    data.response_types.forEach((type, index) => {
        const optionWrapper = document.createElement('div');
        optionWrapper.className = 'response-type-option';

        const input = document.createElement('input');
        input.type = 'radio';
        input.name = 'responseType';
        input.value = type.name;
        input.id = `responseType_${index}`;
        if (index === 0) {
            input.checked = true; // Select the first option by default
        }

        const label = document.createElement('label');
        label.htmlFor = input.id;
        label.className = 'response-type-label';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'response-type-name';
        nameSpan.textContent = type.name;

        const aboutSpan = document.createElement('span');
        aboutSpan.className = 'response-type-about';
        aboutSpan.textContent = type.about;

        label.appendChild(nameSpan);
        label.appendChild(aboutSpan);

        optionWrapper.appendChild(input);
        optionWrapper.appendChild(label);

        responseTypeContainer.appendChild(optionWrapper);

        // Add event listener to track response type change
        input.addEventListener('change', function() {
            gtag('event', 'change', {
                'event_category': 'Settings',
                'event_label': 'Response Type Changed',
                'value': type.name
            });
        });
    });
}

function createLinkElement(url, text) {
    const link = document.createElement('a');
    link.href = url;
    link.textContent = text;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    return link;
}

document.getElementById('questionForm').onsubmit = async function(event) {
    event.preventDefault();
    const questionInput = document.getElementById('questionInput').value;
    const responseContainer = document.getElementById('response');
    responseContainer.innerHTML = '';  // Clear previous response

    // Get the selected response type
    const responseType = document.querySelector('input[name="responseType"]:checked').value;

    // Get the CSRF token
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

    // Show loading indicator before initiating the fetch
    responseContainer.innerHTML = '<div class="loading-spinner"></div>';
    responseContainer.style.display = 'block';

    // Track form submission event
    gtag('event', 'submit', {
        'event_category': 'Queries',
        'event_label': 'Query Submitted',
        'value': responseType
    });

    try {
        console.log('Sending request to /api/ask with:', { question: questionInput, response_type: responseType });

        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken  // Include CSRF token in the headers
            },
            body: JSON.stringify({ question: questionInput, response_type: responseType })
        });

        console.log('Received response:', response);
        console.log('Response status:', response.status);
        const responseText = await response.text();
        console.log('Response text:', responseText);

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${responseText}`);
        }

        // Clear the loading indicator
        responseContainer.innerHTML = '';

        const data = JSON.parse(responseText); // Manually parse JSON
        let { answer, warning, links } = data;

        if (warning) {
            const warningElement = document.createElement('div');
            warningElement.className = 'warning-message';
            warningElement.innerHTML = `<strong>Note:</strong> ${warning}`;
            responseContainer.appendChild(warningElement);
        }

        const answerElement = document.createElement('div');
        answerElement.className = 'answer-message';
        answerElement.innerHTML = answer.replace(/\n/g, '<br>'); // Preserve line breaks
        responseContainer.appendChild(answerElement);

        if (links && links.length > 0) {
            const linksContainer = document.createElement('div');
            linksContainer.className = 'links-container';
            linksContainer.innerHTML = '<strong>Resources:</strong> ';
            links.forEach(link => {
                const linkElement = createLinkElement(link.url, link.text);
                linksContainer.appendChild(linkElement);
            });
            responseContainer.appendChild(linksContainer);
        }

        responseContainer.style.display = 'block';
    } catch (error) {
        console.error('Error during fetch:', error);
        responseContainer.innerHTML = `<div class="error-message">${error.message}</div>`;
    }
};

// Allow the user to submit the form by pressing Enter
document.getElementById('questionInput').addEventListener('keypress', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        document.querySelector('form button[type="submit"]').click();
    }
});

// Add event listeners for the reload buttons
document.getElementById('reloadConfig').addEventListener('click', function() {
    fetchData('/api/reload-config');

    // Track reload config button click
    gtag('event', 'click', {
        'event_category': 'Button',
        'event_label': 'Reload Config'
    });
});

document.getElementById('reloadData').addEventListener('click', function() {
    fetchData('/api/reload-data');

    // Track reload data button click
    gtag('event', 'click', {
        'event_category': 'Button',
        'event_label': 'Reload Data'
    });
});

// Load response types on page load
loadResponseTypes();
