# Scrape instagram profiles in batches

This script uses the excellent [instaloader](https://instaloader.github.io/) to scrape data for a given list of usernames
and exports the results as two CSV files and a graph file:

* One CSV file (`accounts.csv`) containing one row per scraped username, with metadata such as biography, number of
  followers, number of posts, et cetera
* One CSV file (`posts.csv`) containing one row per post, with metadata such as post URL, caption, hashtags, likes, et
  cetera
* One Gephi-compatible GDF file (`follower-network.gdf`) containing a graph representing followers and followees for 
  each account. This is a directed graph with accounts as nodes, and directed edges representing follower/followee 
  relationships. If account `internetperson` follows account `webuser`, an edge from `internetperson` to `webuser` is 
  created.
  
These files will, by default, be created in the folder you run the script from.

## Configuration
This script requires Python 3. It also requires instaloader to work. You can easily install it with pip from the 
script's directory:

```pip install -r requirements.txt```

You may need to use `pip3` if `pip` does not work or uses Python 2 (you can check this by running `pip -V`). Using this 
command will ensure the instaloader version required by the script is installed.

Due to Instagram's limitations, the scrape needs to be done 'from' a logged-in account. To this end, you need to create
a file `config.py` in the script's folder containing your Instagram username and password. You can use 
`config.py-example` as a template.

Once you have created this file, run the script this way:

`python scrape-batch.py --batchfile batch.txt`

This will scrape all accounts listed in `batch.txt`, assuming one account per line. If you want the result files to be
created elsewhere, you can pass an additional argument:

`python scrape-batch.py --batchfile batch.txt --output /home/sam/scrape-results`

This will create the files in the folder `/home/sam/scrape-results`. The folder needs to exist.

## License etc
This script was developed by the [Digital Methods Initiative](https://digitalmethods.net) and is licensed with the MIT 
License. See LICENSE for more information.