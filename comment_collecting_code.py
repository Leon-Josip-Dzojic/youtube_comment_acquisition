import googleapiclient.discovery
import pandas as pd
# import openpyxl as xl

api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = "Your API Key"

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=DEVELOPER_KEY)


# Retrieves all the video ids from the entire channel (given the channel id).
# More precisely it retrieves the ids of all the videos from the channel's uploaded playlist.
def getVideoIds(channel):
    videos = []

    requestUploadsPlaylist = youtube.channels().list(
        part="contentDetails",
        id=channel
    )

    response = requestUploadsPlaylist.execute()
    uploads_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    request_video_ids = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=uploads_playlist_id,
        maxResults = 50
    )

    response_2 = request_video_ids.execute()
    for item in response_2["items"]:
        videos.append(item["contentDetails"]["videoId"])
    
    while True:
        try:
            nextPageToken = response_2['nextPageToken']
        except KeyError:
            print("No next page.")
            break

        nextRequest = youtube.playlistItems().list(
            part="contentDetails", 
            playlistId=uploads_playlist_id, 
            maxResults=50, 
            pageToken=nextPageToken)
        response_2 = nextRequest.execute()

        for item in response_2["items"]:
            videos.append(item["contentDetails"]["videoId"])

    return videos


def getComments(video):
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video,
        maxResults=100
  )

    comments = []

    # Exception handling for the case where the comments on the video have been disabled.
    # Unfortunately, the API does not offer the option to check if the comments are disabled beforehand.
    # TODO get a more specific error to raise.
    # TODO track these videos to get a better data overview.
    try:
        response = request.execute()
    except:
        comments.append([
            "Commends on this video are disabled!",
            "Commends on this video are disabled!",
            "Commends on this video are disabled!",
            "Commends on this video are disabled!",
            "Commends on this video are disabled!",
            "Commends on this video are disabled!"
        ])
        video_comments = pd.DataFrame(comments, columns=['author', 'updated_at', 'like_count', 'text','video_id','public'])
        print("The comments on the video: " + video + " are disabled.")
        return video_comments


    # Execute the request.

    # Get the comments from the response.
    for item in response['items']:
        comment = item['snippet']['topLevelComment']['snippet']
        public = item['snippet']['isPublic']
        comments.append([
            comment['authorDisplayName'],
            comment['publishedAt'],
            comment['likeCount'],
            comment['textOriginal'],
            comment['videoId'],
            public
        ])

    while True:
        try:
            nextPageToken = response['nextPageToken']
        except KeyError:
            print("No next page.")
            break

        # Create a new request object with the next page token.
        nextRequest = youtube.commentThreads().list(part="snippet", videoId=video, maxResults=100, pageToken=nextPageToken)

        # Execute the next request.
        # TODO handle this better. Analyse exceptions so that data can be profiled correctly.
        try:
            response = nextRequest.execute()
        except:
            video_comments = pd.DataFrame(comments,
                                          columns=['author', 'updated_at', 'like_count', 'text', 'video_id', 'public'])
            return video_comments

        # Get the comments from the next response.
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            public = item['snippet']['isPublic']
            comments.append([
                comment['authorDisplayName'],
                comment['publishedAt'],
                comment['likeCount'],
                comment['textOriginal'],
                comment['videoId'],
                public
        ])

    video_comments = pd.DataFrame(comments, columns=['author', 'updated_at', 'like_count', 'text','video_id','public'])
    return video_comments

def formatData(comment_data):
    # Some YouTube comments have extra blank line and or line breaks. People use these to force a "read more" formatting style
    # in YouTube. It causes issues for the output in .csv files.
    formatted_data = comment_data.replace(to_replace={"text": {"\n\s*\n": "\n", "\n": " ", "\r": " "}}, regex=True)
    return formatted_data

def main():
    all_comments = pd.DataFrame()
    commentDataPathCSV = r"comment_data.csv"
    commentDataPathXLSX = r"comment_data.xlsx"
    videoIdDataPath = r"video_id.csv"

    # All the video ids are stores in this array
    videos = getVideoIds("Channel ID") # For example: 'UCgut0aj_YW9tJNKJ8Rd7EoA' from a smaller channel.
    video_df = pd.DataFrame(videos, columns=["Video_Id"])
    video_df.to_csv(path_or_buf=videoIdDataPath)

    for i in videos:
        video_comments = getComments(i)
        all_comments = pd.concat([all_comments, video_comments])

    all_comments.info()
    all_comments = formatData(all_comments)
    all_comments.to_csv(path_or_buf=commentDataPathCSV, sep=" ")
    all_comments.to_excel(commentDataPathXLSX)


main()


