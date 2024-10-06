// Function to save the cached data in the hidden input
document.getElementById('saveBtn').addEventListener('click', function () {
    // Convert the cached data into a JSON string
    const jsonData = JSON.stringify(cachedData);

    // Set the hidden input's value to the JSON data
    document.getElementById('cachedDataInput').value = jsonData;

    alert('Cached data saved! Now you can download the JSON file.');
});
