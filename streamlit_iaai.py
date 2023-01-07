import os
os.system("playwright install chromium")
from playwright.sync_api import Playwright, sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
from latest_user_agents import get_random_user_agent
from time import sleep
import streamlit as st

st.set_page_config(page_title= 'IAAI Scraper', page_icon=":smile:")
hide_menu = """
<style>
#MainMenu {
    visibility:hidden;}
footer {
    visibility:hidden;}
</style>
"""
st.markdown(hide_menu, unsafe_allow_html=True)

def clean_data(your_data):
    vins = [x.replace('******', '') for x in your_data['Vin']]
    source = ['IAAI' for x in your_data]
    your_data['Vin'] = vins
    source = []
    for x in range(len(your_data.index)):
        source.append('IAAI')
    your_data['Source'] = source

def scraper():
    item_list = []
    with sync_playwright() as playwright:
        chrome = playwright.chromium
        browser = chrome.launch()
        #context = browser.new_context(storage_state="auth.json")
        context = browser.new_context()
        page = context.new_page()
        page.set_extra_http_headers({'User-Agent': get_random_user_agent()})
        page.goto(f'{link_to_scrape}', timeout=1000000, wait_until='networkidle')
        page.get_by_role("button", name="Accept Cookies").click()

        next_page = page.locator('.btn-next')
        n = 0
        col1, col2 = st.columns(2)
        progress = col1.metric('Pages scraped', 0)
        while True:
            n = n + 1
            progress.metric('Pages scraped', n)
            try:
                page.frame_locator("#kampyleInvite").get_by_role("button", name="Close Survey").click(timeout=1000)
                sleep(5)
            except:
                pass

            soup = BeautifulSoup(page.content(), 'lxml')
            soup = soup.select_one('.table-body.border-l.border-r')
            cards = soup.select('.table-row.table-row-border')
            for card in cards:
                name = card.select_one('h4').text.strip()
                year = name.split(' ')[0].strip()
                make_model = name.replace(year, '').strip()

                lists = []
                for x in card.select('.data-list__item span'):
                    try:
                        test_ = x['title']
                        lists.append(x)
                    except:
                        pass

                for y in lists:
                    if 'Please log in as a buyer' in y['title']:
                        if len(y.text.strip()) > 6:
                            vin = y.text.strip()
                    elif 'Odometer' in y['title']:
                        odometer = y.text.strip()
                    elif 'Title/Sale Doc' in y['title']:
                        title = y.text.strip()
                    elif 'Fuel Type' in y['title']:
                        type_ = y.text.strip()
                    elif 'ACV' in y['title']:
                        acv = y.text.strip()
                    elif 'Branch' in y['title']:
                        location = y.text.strip()
                    else:
                        pass
                
                items = {
                    'Name': name,
                    'Year': year,
                    'Make-model': make_model,
                    'Vin': vin,
                    'Odometer': odometer,
                    'Title': title,
                    'Type': type_,
                    'Value': acv,
                    'Location': location
                }
                item_list.append(items)

            if next_page.is_disabled():
                break
            page.click('.btn-next')
            sleep(5)
            page.wait_for_load_state('networkidle')
            sleep(5)

        browser.close()

    df = pd.DataFrame(item_list)
    clean_data(df)
    st.dataframe(df)
    col2.metric('Total data scraped', len(df))
    csv = df.to_csv().encode('utf-8')
    st.download_button(
    label = "📥 Download Current Result in csv",
    data = csv,
    file_name = 'iaai.csv',
    mime='text/csv',
)


st.title('IAAI SCRAPER')
st.caption('A scraper to car information from IAAI.com')
st.caption('Note that you might get an error is you paste link other than the listing link')

with st.form('myForm'):
    link_to_scrape = st.text_input('Listing Link', placeholder='https://www.iaai.com/Search?url=6pTzI3QI7DHyTxk3hgltp0Jw8Rkj%2fZgdn3VgK4AZlFs%3d')

    submitted = st.form_submit_button("Submit")

if submitted:
    scraper()
    st.balloons()
    st.success('Done!')
    
