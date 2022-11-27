
stopwords_path = './agregator/parcer/globalpars/stopwords/'

class Ya:
    """Search-engine class."""
    name = 'Yandex News'
    query_start = 'https://dzen.ru/news/search?issue_tld=ru&text='
    article_class = 'mg-snippet__url'
    cookies = {
        'news_search_sort_by': 'date',
        'nc': 'search-visits-per-week=3:1669567073000',
        '_yasc': 'soOuHSAaz0WGpasgJfbQOylICUA1tHcB0ImTpeYVo5iVF4xXwTW3CkdGgls=',
        'sso_checked': '1',
        'Session_id': 'noauth:1669364386',
        'yandex_login': '',
        'ys': 'c_chck.1077622029',
        'yandexuid': '9102950251669297428',
        'mda2_beacon': '1669364386932',
        '_ym_uid': '1669364391237237702',
        '_ym_d': '1669364391',
        'tmr_lvid': '944eb7f87a663a62bf383f90148f7076',
        'tmr_lvidTS': '1669364391532',
        'crookie': 'sUh1T5cEuUFxJfzDPU8CekIIs+WftMxpg/bIiJHNYDPlAUDpHHm+xgadZG2C3ZzLA0GCzgqRF9IVeTTrDts55XJW1b4=',
        'cmtchd': 'MTY2OTM2NDM5MjY2MQ==',
        'KIykI': '1',
        '_ym_isad': '1',
        'tmr_detect': '1%7C1669567075857',
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        # Requests sorts cookies= alphabetically
        # 'Cookie': 'news_search_sort_by=date; nc=search-visits-per-week=3:1669567073000; _yasc=soOuHSAaz0WGpasgJfbQOylICUA1tHcB0ImTpeYVo5iVF4xXwTW3CkdGgls=; sso_checked=1; Session_id=noauth:1669364386; yandex_login=; ys=c_chck.1077622029; yandexuid=9102950251669297428; mda2_beacon=1669364386932; _ym_uid=1669364391237237702; _ym_d=1669364391; tmr_lvid=944eb7f87a663a62bf383f90148f7076; tmr_lvidTS=1669364391532; crookie=sUh1T5cEuUFxJfzDPU8CekIIs+WftMxpg/bIiJHNYDPlAUDpHHm+xgadZG2C3ZzLA0GCzgqRF9IVeTTrDts55XJW1b4=; cmtchd=MTY2OTM2NDM5MjY2MQ==; KIykI=1; _ym_isad=1; tmr_detect=1%7C1669567075857',
        'Referer': 'https://dzen.ru/news/search?issue_tld=ru&text=%D1%81%D0%B5%D0%B3%D0%BE%D0%B4%D0%BD%D1%8F+date%3A20221123..20221125&filter_date=1669150800000%2C1669323600000',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    query_end = (
        f'+date%3A{0}..{0}'
        '&flat=1&sortby=date&filter_date='
        f'{1}%2C{1}'
    )

    @staticmethod
    def get_article(el):
        """Load link and title, using Yandex News configuration."""
        link = el['href']
        tail = link[link.find('utm') - 1:]
        link = link.replace(tail, '')
        title = el.div.span.text
        return link, title
