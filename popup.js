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
    const channelBranding = channelData.items[0].brandingSettings;
    const channelContentDetails = channelData.items[0].contentDetails;

    const analyticsMessage = `
      Channel Name: ${channelSnippet.title}
      Channel Description: ${channelSnippet.description}
      Subscriber Count: ${channelStats.subscriberCount}
      Total Views: ${channelStats.viewCount}
      Total Videos: ${channelStats.videoCount}
      
      Video Title: ${videoSnippet.title}
      Video View Count: ${videoStats.viewCount}
      Video Like Count: ${videoStats.likeCount}
      Video Comment Count: ${videoStats.commentCount}
      Video Duration: ${videoContentDetails.duration}
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
    const analyticsMessage = await fetchAnalytics(tabUrl);
    analyticsDataDiv.textContent = analyticsMessage;
  });
});
