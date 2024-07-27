async function fetchAnalytics(tabUrl) {
  function getVideoIdFromUrl(url) {
    const urlObj = new URL(url);
    return urlObj.searchParams.get("v");
  }

  const videoId = getVideoIdFromUrl(tabUrl);
  if (!videoId) {
    console.error("No video ID found in the URL");
    return "No video ID found in the URL";
  }

  try {
    const response = await fetch(chrome.runtime.getURL('config.json'));
    const config = await response.json();
    const apiKey = config.apiKey;

    const videoApiUrl = `https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet,contentDetails&id=${videoId}&key=${apiKey}`;
    const videoResponse = await fetch(videoApiUrl);
    const videoData = await videoResponse.json();

    if (videoData.items.length === 0) {
      console.error("No video data found");
      return "No video data found";
    }

    const videoStats = videoData.items[0].statistics;
    const videoSnippet = videoData.items[0].snippet;
    const videoContentDetails = videoData.items[0].contentDetails;
    const channelId = videoSnippet.channelId;

    const channelApiUrl = `https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet,brandingSettings,contentDetails&id=${channelId}&key=${apiKey}`;
    const channelResponse = await fetch(channelApiUrl);
    const channelData = await channelResponse.json();

    if (channelData.items.length === 0) {
      console.error("No channel data found");
      return "No channel data found";
    }

    const channelStats = channelData.items[0].statistics;
    const channelSnippet = channelData.items[0].snippet;

    const analyticsMessage = `
      <div class="section-title">Channel Name:</div>
      <div class="section-content">${channelSnippet.title}</div>
      <div class="section-title">Channel Description:</div>
      <div class="section-content">${channelSnippet.description}</div>
      <div class="section-title">Subscriber Count:</div>
      <div class="section-content">${channelStats.subscriberCount.toLocaleString()}</div>
      <div class="section-title">Total Views:</div>
      <div class="section-content">${channelStats.viewCount.toLocaleString()}</div>
      <div class="section-title">Total Videos:</div>
      <div class="section-content">${channelStats.videoCount.toLocaleString()}</div>
      <div class="section-title">Video Title:</div>
      <div class="section-content">${videoSnippet.title}</div>
      <div class="section-title">Video View Count:</div>
      <div class="section-content">${videoStats.viewCount.toLocaleString()}</div>
      <div class="section-title">Video Like Count:</div>
      <div class="section-content">${videoStats.likeCount ? videoStats.likeCount.toLocaleString() : 'N/A'}</div>
      <div class="section-title">Video Comment Count:</div>
      <div class="section-content">${videoStats.commentCount ? videoStats.commentCount.toLocaleString() : 'N/A'}</div>
      <div class="section-title">Video Duration:</div>
      <div class="section-content">${videoContentDetails.duration}</div>
    `;

    return analyticsMessage;
  } catch (error) {
    console.error("Error fetching YouTube data", error);
    return "Error fetching YouTube data";
  }
}

document.addEventListener('DOMContentLoaded', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    const tabUrl = tabs[0].url;
    const analyticsDataDiv = document.getElementById('analytics-data');
    const audioStatusDiv = document.getElementById('audio-status');
    const transcriptionDiv = document.getElementById('transcription-data');
    
    try {
      const analyticsMessage = await fetchAnalytics(tabUrl);
      analyticsDataDiv.innerHTML = analyticsMessage;
      analyticsDataDiv.classList.remove('loading');
    } catch (error) {
      analyticsDataDiv.textContent = "Error loading analytics data.";
      analyticsDataDiv.classList.remove('loading');
      console.error('Error in fetchAnalytics:', error);
    }

    try {
      const transcription = await fetchMp3Base64(tabUrl);
      audioStatusDiv.textContent = "Audio processing done!";
      audioStatusDiv.classList.remove('loading');
      transcriptionDiv.textContent = transcription;
    } catch (error) {
      audioStatusDiv.textContent = "Error processing audio.";
      audioStatusDiv.classList.remove('loading');
      transcriptionDiv.textContent = error.message;
      console.error('Error in fetchMp3Base64:', error);
    }
  });
});


async function fetchMp3Base64(tabUrl) {
  return new Promise((resolve, reject) => {
    if (!chrome.runtime || !chrome.runtime.sendMessage) {
      return reject(new Error('Chrome runtime or sendMessage API is not available.'));
    }
    if (!chrome.storage || !chrome.storage.local) {
      return reject(new Error('Chrome storage or storage.local API is not available.'));
    }

    chrome.runtime.sendMessage(
      { action: "fetchMp3", videoUrl: tabUrl },
      (response) => {
        if (chrome.runtime.lastError) {
          return reject(new Error(chrome.runtime.lastError.message));
        } else if (response.error) {
          return reject(new Error(response.error));
        } else if (!response.success || !response.storageKey) {
          return reject(new Error("No success or storageKey found in the response"));
        } else {
          // Retrieve data from Chrome local storage
          chrome.storage.local.get(response.storageKey, (result) => {
            if (chrome.runtime.lastError) {
              return reject(new Error(chrome.runtime.lastError.message));
            } else {
              const transcription = result[response.storageKey];
              if (!transcription) {
                return reject(new Error("No transcription found in local storage"));
              } else {
                resolve(transcription);
                // Optionally remove the stored data after retrieval to clean up
                chrome.storage.local.remove(response.storageKey);
              }
            }
          });
        }
      }
    );
  });
}

document.addEventListener('DOMContentLoaded', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    const tabUrl = tabs[0].url;
    const analyticsDataDiv = document.getElementById('analytics-data');
    const audioStatusDiv = document.getElementById('audio-status');
    const transcriptionDiv = document.getElementById('transcription-data');
    
    try {
      const analyticsMessage = await fetchAnalytics(tabUrl);
      analyticsDataDiv.textContent = analyticsMessage;
    } catch (error) {
      analyticsDataDiv.textContent = "Error loading analytics data.";
      console.error('Error in fetchAnalytics:', error);
    }

    try {
      const transcription = await fetchMp3Base64(tabUrl);
      audioStatusDiv.textContent = "Audio processing done!";
      transcriptionDiv.textContent = transcription;
    } catch (error) {
      audioStatusDiv.textContent = "Error processing audio.";
      transcriptionDiv.textContent = error.message;
      console.error('Error in fetchMp3Base64:', error);
    }
  });
});
