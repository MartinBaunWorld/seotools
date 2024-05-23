#!/usr/bin/python3

"""
sitemap2bing.py is a little tool that helps you submit your sitemap to bing.
Bing really likes to receive these submissions and it'll help with ranking higher.

Example usage:

```
python3 sitemap2bing.py YOUR_BING_KEY https://martinbaun.com/sitemap.xml
```
"""

from urllib.parse import urlparse
from requests import get, post
from datetime import datetime
from traceback import format_exc

from bs4 import BeautifulSoup
from docopt import docopt


def read_or_default(path, default):
    try:
        with open(path, 'r') as f:
            return f.read()
    except:
        return default


def write(path, msg):
    with open(path, 'w') as f:
        return f.write(msg)


def cutoff(sitename, urls):
    """
        This ensures only 99 per chunks are sent each request
    """
    MAX_CHUNKS = 99
    # TODO: this seems to work, but is ugly.
    if len(urls) < MAX_CHUNKS:
        return urls

    start = int(read_or_default(f'/tmp/{sitename}.txt', 0))
    end = start + MAX_CHUNKS 
    if end > len(urls):
        new_start = 0
    else:
        new_start = end

    write(f'/tmp/{sitename}.txt', str(new_start))
        

    return urls[start:end]


def send_sitemap_links(content, bingauth):
    url = f"https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlbatch?apikey={bingauth}"
    res = post(url, json=content)

    print(f"STATUS: {res.status_code}\n"
          f"RESPONSE: {res.text}\n")


def parse_xml_sitemap(content, urls, max_deep_level):
    soup = BeautifulSoup(content, 'xml')
    locs = soup.find_all('loc')

    for loc in locs:
        url = loc.text
        urls.append(url)
        if url.endswith('.xml') and max_deep_level > 0:
            res = get(url)
            max_deep_level -= 1
            parse_xml_sitemap(res.content, urls, max_deep_level)

    return urls


def main(sitemap, bingauth, max_deep_level):
    try:
        print(f"{datetime.now().isoformat()} {sitemap}")

        res = get(sitemap)
        urls = parse_xml_sitemap(res.content, [], max_deep_level)
        if not urls:
            return
        
        site_url = urlparse(urls[0])
        urls = cutoff(site_url.hostname, urls)
        bing_data = dict(
            siteUrl=f"{site_url.scheme}://{site_url.hostname}",
            urlList=urls,
        )
        send_sitemap_links(bing_data, bingauth)
    except: # noqa
        print(f"While processing sitemap the following error occurred:\n"
              f"{format_exc()}\n\n")
        exit(1)


doc = """bing

Usage:
  sitemap2bing.py <bingauth> <sitemap> [<max_deep_level>]

Options:
  -h --help     Show this screen.
"""


if __name__ == "__main__":
    arguments = docopt(doc)

    max_deep_level = arguments['<max_deep_level>'] or 3
    sitemap = arguments['<sitemap>']
    bingauth = arguments['<bingauth>']

    main(sitemap, bingauth, max_deep_level)
