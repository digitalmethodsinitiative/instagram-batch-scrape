import instaloader
import argparse
import pathlib
import sys
import csv

config_path = pathlib.Path(__file__, "..", "config.py").resolve()
if not config_path.exists():
	print("No config.py file found. You can create it by copying or renaming")
	print("config.py-example and editing the values in it.")
	sys.exit(1)

import config

cli = argparse.ArgumentParser()
cli.add_argument("--batchfile", "-b", required=True, help="File containing entities to scrape, one per line")
cli.add_argument("--output", "-o",
				 help="Location to create result files in. If left empty, the working directory is used.")
args = cli.parse_args()

batch_file = pathlib.Path(args.batchfile).resolve()
if not batch_file.exists():
	print("Batch file ('%s') not found." % str(batch_file))
	sys.exit(1)

output_path = pathlib.Path(args.output).resolve() if args.output else pathlib.Path(__file__, "..").resolve()
if not output_path.exists() or not output_path.is_dir():
	print("Given output path (%s) is not a valid directory." % str(output_path))
	sys.exit(1)

instagram = instaloader.Instaloader(download_comments=False, download_pictures=False, download_videos=False,
									download_video_thumbnails=False, save_metadata=False)
try:
	instagram.login(config.USERNAME, config.PASSWORD)
except (instaloader.BadCredentialsException, instaloader.InvalidArgumentException):
	print("Invalid username or password configured in config.py. Cannot scrape.")
	sys.exit(1)
except instaloader.TwoFactorAuthRequiredException:
	print("This account (%s) requires two-factor authentication. The scraper is not" % (config.USERNAME))
	print("able to handle 2FA at this time. Please disable two-factor authentication for this")
	print("account and try again.")
	sys.exit(1)

usernames = set()
with batch_file.open() as input:
	for username in input:
		if not username.strip():
			continue
		usernames.add(username.strip())

# initialise result variables and files
# user and post data is written to a CSV file directly, followers/followees are
# kept in memory until the end to write one big graph file
user_file = output_path.joinpath("accounts.csv").open("w")
user_writer = csv.DictWriter(user_file, fieldnames=["username", "url",
													"url_profile_pic", "full_name", "userid", "is_verified",
													"has_viewable_story", "has_public_story",
													"biography", "media_count", "igtv_count", "followers", "followees"])
user_writer.writeheader()

post_file = output_path.joinpath("posts.csv").open("w")
post_writer = csv.DictWriter(post_file, fieldnames=["shortcode", "username", "date_utc", "url_thumbnail", "url_media",
													"is_video", "is_sponsored", "hashtags", "mentions", "caption",
													"video_view_count", "video_length", "likes",
													"comments", "likes+comments", "location_name", "location_latlong"])
post_writer.writeheader()

follower_graph = []
follow_usernames = set()
user_ids = {}

# start scraping
print("Scraping %i usernames, %i posts per user." % (len(usernames), config.POSTS_PER_USERNAME))
for username in usernames:
	print("Scraping %s..." % username)

	try:
		profile = instaloader.Profile.from_username(instagram.context, username)
	except instaloader.ProfileNotExistsException:
		print("Profile %s does not exist, skipping." % username)
		continue

	user_ids[username] = profile.userid

	for follower in profile.get_followers():
		pair = [follower.username, username]
		follower_graph.append(pair)
		follow_usernames.add(follower.username)
		follow_usernames.add(username)
		user_ids[follower.username] = follower.userid

	for followee in profile.get_followees():
		pair = [username, followee.username]
		follower_graph.append(pair)
		follow_usernames.add(followee.username)
		follow_usernames.add(username)
		user_ids[followee.username] = followee.userid

	profile_info = {
		"username": username,
		"url": "https://instagram.com/%s" % username,
		"url_profile_pic": profile.profile_pic_url,
		"full_name": profile.full_name,
		"userid": profile.userid,
		"is_verified": "yes" if profile.is_verified else "no",
		"has_viewable_story": "yes" if profile.has_viewable_story else "no",
		"has_public_story": "yes" if profile.has_public_story else "no",
		"biography": profile.biography,
		"media_count": profile.mediacount,
		"igtv_count": profile.igtvcount,
		"followers": profile.followers,
		"followees": profile.followees,
	}

	user_writer.writerow(profile_info)

	processed = 1
	for post in profile.get_posts():
		if processed > config.POSTS_PER_USERNAME:
			break

		print("...scraping info for post %s" % post.shortcode)

		post_info = {
			"shortcode": post.shortcode,
			"username": username,
			"date_utc": post.date_utc.strftime("%Y-%m-%d %H:%M"),
			"url_thumbnail": post.url,
			"url_media": post.video_url if post.is_video else post.url,
			"is_video": "yes" if post.is_video else "no",
			"is_sponsored": post.is_sponsored,
			"hashtags": ",".join(post.caption_hashtags),
			"mentions": ",".join(post.caption_mentions),
			"caption": post.caption,
			"video_view_count": post.video_view_count if post.is_video else 0,
			"video_length": post.video_duration if post.is_video else 0,
			"likes": post.likes,
			"comments": post.comments,
			"likes+comments": (post.likes + post.comments),
			"location_name": post.location.name if post.location else "",
			"location_latlong": " ".join((str(post.location.lat), str(post.location.lng))) if post.location else ""
		}

		processed += 1

		post_writer.writerow(post_info)

	print("...scraped %i posts for %s" % (processed - 1, username))

user_file.close()
post_file.close()

print("Done scraping. Writing follower/followee graph.")
with output_path.joinpath("follower-network.gdf").open("w") as output:
	output.write("nodedef>name VARCHAR,userid VARCHAR\n")
	for username in follow_usernames:
		output.write("%s,%s\n" % (username, user_ids[username]))

	output.write("edgedef>from VARCHAR,to VARCHAR,directed BOOLEAN\n")
	for pair in follower_graph:
		output.write("%s,%s,true\n" % (pair[0], pair[1]))

print("Done!")
