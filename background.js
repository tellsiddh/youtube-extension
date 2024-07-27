chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "fetchMp3") {
    fetch('http://127.0.0.1:5000/fetch_mp3', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Extension-Id': chrome.runtime.id
      },
      body: JSON.stringify({ video_url: request.videoUrl })
    })
    .then(response => {
      if (!response.ok) {
        return response.text().then(text => {
          throw new Error(`HTTP error! status: ${response.status}, body: ${text}`);
        });
      }
      return response.json();
    })
    .then(data => {
      if (data.error) {
        throw new Error(data.error);
      }
      sendResponse({ 
        base64_webm: data.base64_webm, 
        transcription_response: data.transcription_response || data.response.transcription_text
      });
    })
    .catch(error => {
      console.error('Detailed error in background script:', error);
      sendResponse({ error: error.message });
    });

    return true;  // Indicates that the response is sent asynchronously
  }
});
