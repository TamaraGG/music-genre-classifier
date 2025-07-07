document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const audioFileInput = document.getElementById('audio-file-input');
    const fileNameDisplay = document.getElementById('file-name-display');
    const loader = document.getElementById('loader');
    const resultSection = document.getElementById('result-section');
    const topGenreSpan = document.getElementById('top-genre');
    const probabilitiesList = document.getElementById('probabilities-list');
    const errorSection = document.getElementById('error-section');
    const errorMessage = document.getElementById('error-message');
    const historyTableBody = document.getElementById('history-table-body');

    audioFileInput.addEventListener('change', () => {
        if (audioFileInput.files.length > 0) {
            fileNameDisplay.textContent = audioFileInput.files[0].name;
            fileNameDisplay.style.fontStyle = 'normal';
            fileNameDisplay.style.color = '#e0e0e0';
        } else {
            fileNameDisplay.textContent = 'File not selected';
            fileNameDisplay.style.fontStyle = 'italic';
            fileNameDisplay.style.color = '#aaa';
        }
    });

    async function fetchAndDisplayHistory() {
        try {
            const response = await fetch('/api/history');
            if (!response.ok) throw new Error('Failed to load history');
            const history = await response.json();
            historyTableBody.innerHTML = '';
            if (history.length === 0) {
                historyTableBody.innerHTML = '<tr><td colspan="3">No history yet.</td></tr>';
                return;
            }
            history.forEach(item => {
                const row = document.createElement('tr');
                const formattedDate = new Date(item.predictionTimestamp).toLocaleString('en-US');
                row.innerHTML = `<td>${item.fileName}</td><td>${item.predictedGenre}</td><td>${formattedDate}</td>`;
                historyTableBody.appendChild(row);
            });
        } catch (error) {
            console.error('Error loading history:', error);
            historyTableBody.innerHTML = '<tr><td colspan="3">Error loading history.</td></tr>';
        }
    }

    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const file = audioFileInput.files[0];
        if (!file) {
            showError('Please select a file.');
            return;
        }
        loader.style.display = 'block';
        resultSection.style.display = 'none';
        errorSection.style.display = 'none';
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch('/api/upload', { method: 'POST', body: formData });
            if (!response.ok) throw new Error(`Server error: ${response.status} ${response.statusText}`);
            const data = await response.json();
            displayResult(data);
            fetchAndDisplayHistory();
        } catch (error) {
            console.error('Error uploading file:', error);
            showError('Failed to get the result. Please try again.');
        } finally {
            loader.style.display = 'none';
        }
    });

    function displayResult(data) {
        topGenreSpan.textContent = data.identifiedGenre;
        probabilitiesList.innerHTML = '';
        const sortedProbabilities = Object.entries(data.allProbabilities).sort(([, a], [, b]) => b - a);
        for (const [genre, probability] of sortedProbabilities) {
            const listItem = document.createElement('li');
            const percentage = (probability * 100).toFixed(2);
            listItem.innerHTML = `<span>${genre}</span> <strong>${percentage}%</strong>`;
            probabilitiesList.appendChild(listItem);
        }
        resultSection.style.display = 'block';
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorSection.style.display = 'block';
    }

    fetchAndDisplayHistory();
});