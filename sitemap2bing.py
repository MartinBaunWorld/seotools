#!/usr/bin/python3

from urllib.parse import urlparse
from requests import get, post
from datetime import datetime
from traceback import format_exc

from bs4 import BeautifulSoup
from docopt import docopt


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
        bing_data = dict(
            siteUrl=f"{site_url.scheme}://{site_url.hostname}",
            urlList=[url for url in urls if '/tags/' not in url],
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
