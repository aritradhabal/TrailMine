import streamlit as st
import json
import requests
# import pandas as pd
import fireducks.pandas as pd
from streamlit_agraph import agraph, Config, Node, Edge
import time
import datetime
from moralis import evm_api
import plotly.express as px
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from collections import defaultdict
import streamlit_lottie
import pickle
import os
# from streamlit_star_rating import st_star_rating
from streamlit_extras.app_logo import add_logo
from streamlit_extras.dataframe_explorer import dataframe_explorer
# from neo4j import GraphDatabase

st.set_page_config(
    page_title="Tra1lM1ine Analyzer",
    page_icon=":material/decimal_increase:",
    layout="wide",
    # initial_sidebar_state="",
    # menu_items={
    #     'Get Help': 'https://www.extremelycoolapp.com/help',
    #     'Report a bug': "https://www.extremelycoolapp.com/bug",
    #     'About': "# This is a header. This is an *extremely* cool app!"
    # }
)




st.title("Tra1lM1ine Analyzer", anchor=False)

# variables
# API_KEY_1 = st.secrets["api"]["api_key"]

# # api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjczNzBjMTFjLTU5ODAtNGVjNy05Y2M3LWY3MmQ4ZDU2NGVkZSIsIm9yZ0lkIjoiNDE1MzYzIiwidXNlcklkIjoiNDI2ODY0IiwidHlwZSI6IlBST0pFQ1QiLCJ0eXBlSWQiOiJkOTJjNDE5Ny0xMjNiLTQxYWItODY4Zi05Y2E4NTI3YWJkNDUiLCJpYXQiOjE3MzMzMzM0MDMsImV4cCI6NDg4OTA5MzQwM30.AvCnuJhwD7pjYOH3vGvGCj_b6hWPSsGrRP0W3qV6ppA"
# api_key = API_KEY_1

api_key = os.environ["API_KEY"]

if 'clicked' not in st.session_state:
    st.session_state.clicked = False

def click_button():
    st.session_state.clicked = True




#the form
with st.form('values'):
    col1,col2 = st.columns([1, 1],gap="medium")
    with col1:
        wallet = st.text_input("Enter wallet address", placeholder="0x...")
        wallet = wallet.lower()
    with col2:
        chain = st.selectbox(
            "Which chain you want to analyze?",
            ("Ethereum", "Polygon"),
            index=0,
            placeholder="Pick the chain...",
        )
    col1,col2, col3 = st.columns([1, 10, 1],gap="small")
    with col2 :
        length_data = st.slider(label = "How much data you want to fetch ?", min_value = 100, max_value = 500, value= 400, step=100)
        length_data = length_data//100

    a, b, c, d, e = st.columns(5, vertical_alignment="bottom")
    with c:
        submit = st.form_submit_button('Analyze ⏳',on_click=click_button, help="Recent transactions will be fetched", type="primary", use_container_width=True)

##############################################################################
# data processing functions starts here
##############################################################################

def date(df):
    df['block_timestamp'] = pd.to_datetime(df['block_timestamp'])
    df['block_timestamp'] = df['block_timestamp'].dt.date
    return df

def remove_first_duplicates(df):

    cols = df.columns.tolist()
    col_indices = {}
    
    for idx, col in enumerate(cols):
        if col not in col_indices:
            col_indices[col] = [idx]
        else:
            col_indices[col].append(idx)
    
    indices_to_drop = []
    for col, indices in col_indices.items():
        if len(indices) > 1:
            indices_to_drop.append(indices[0])
    
    keep_indices = [i for i in range(len(cols)) if i not in indices_to_drop]

    return df.iloc[:, keep_indices]

def data_making(data):
        
        result = data['result']

        df = pd.DataFrame(result)
        df = df.drop(['erc20_transfers', 'native_transfers', 'nft_transfers'], axis='columns')

        result_length = len(result)

        default_data = {
        'token_name': None,
        'token_symbol': None,
        'token_logo': None,
        'token_decimals': None,
        'from_address_entity': None,
        'from_address_entity_logo': None,
        'from_address': None,
        'from_address_label': None,
        'to_address_entity': None,
        'to_address_entity_logo': None,
        'to_address': None,
        'to_address_label': None,
        'address': None,
        'log_index': None,
        'value': None,
        'possible_spam': None,
        'verified_contract': None,
        'security_score': None,
        'direction': None,
        'value_formatted': None
        }

        transfers = []

        for x in range(result_length):
            if len(data['result'][x]['erc20_transfers'])!=0:
                transfers.append(data['result'][x]['erc20_transfers'][0])
            elif len(data['result'][x]['native_transfers'])!=0:
                transfers.append(data['result'][x]['native_transfers'][0])
            else :
                transfers.append(default_data)

        df1 = pd.DataFrame(transfers)
        df = pd.concat([df.reset_index(drop=True), df1.reset_index(drop=True)], axis=1)
        df = remove_first_duplicates(df)
        return df

def df_cleaning(df):

    column_list = df.columns.tolist()

    column_df = []

    if column_list.count('hash') > 0:
        column_df.append('hash')
    if column_list.count('block_timestamp') > 0:
        column_df.append('block_timestamp')
    if column_list.count('summary') > 0:
        column_df.append('summary')
    if column_list.count('token_name') > 0:
        column_df.append('token_name')
    if column_list.count('from_address_entity') > 0:
        column_df.append('from_address_entity')
    if column_list.count('from_address') > 0:
        column_df.append('from_address')
    if column_list.count('to_address_entity') > 0:
        column_df.append('to_address_entity')
    if column_list.count('to_address') > 0:
        column_df.append('to_address')
    if column_list.count('possible_spam') > 0:
        column_df.append('possible_spam')
    if column_list.count('verified_contract') == 0:
        df['verified_contract'] = np.nan
        column_list.append('verified_contract')
    if column_list.count('verified_contract') > 0:
        column_df.append('verified_contract')
    if column_list.count('direction') > 0:
        column_df.append('direction')
    if column_list.count('value_formatted') > 0:
        column_df.append('value_formatted')
    
    df = df[column_df]
    df = date(df)
    df["from_address_entity"] = df["from_address_entity"].fillna("Unknown")
    df["to_address_entity"] = df["to_address_entity"].fillna("Unknown")
    return df

@st.cache_data
def api_query(length_data, wallet, chain, api_key):

    final_df = pd.DataFrame()

    if chain == "Ethereum" :
        chain = "eth"
    elif chain == "Polygon" :
        chain = "polygon"

    cursor = ""
    # api
    for x in range(length_data):
        params = {
            "chain": chain,
            "include_internal_transactions": False,
            "nft_metadata": False,
            "order": "DESC",
            "cursor": cursor,
            "address": wallet,
        }
        data = evm_api.wallets.get_wallet_history(
            api_key=api_key,
            params=params,
        )
        cursor = data["cursor"]
        
        df = data_making(data)
        final_df = pd.concat([final_df, df], ignore_index=True)
        if data['cursor'] is None:
            break
    final_df = df_cleaning(final_df)
    return final_df

##############################################################################
# FILTERING FUNCTIONS
##############################################################################

def filtering_data(df, token):
    # filter_pattern = r'^(Sent|Received) [A-Za-z0-9 ,.:]+(to|from) [A-Za-z0-9 ,.:]+$'
    filter_pattern = r'^(Sent|Received) [A-Za-z0-9 ,.:]+ (to|from) [A-Za-z0-9 ,.:]+$'
    df = df[df['summary'].str.match(filter_pattern)]
    df = df[~df['summary'].str.contains('NFT', na=False)]
    df['token_name'] = df.apply(
        lambda row: token if ( token in row['summary'] and ('Sent' in row['summary'] or 'Received' in row['summary']))
        else row['token_name'], axis=1
    )
    df['verified_contract'] = df['verified_contract'].astype(bool)
    df.loc[df['token_name'] == 'POL', 'verified_contract'] = True
    df = df[df['verified_contract'] == True]
    df = df.drop(["verified_contract", "possible_spam"], axis = 1)
    return df

def filtering_date2(df, df_org):
    mindate = df_org['block_timestamp'].min()
    maxdate = df_org['block_timestamp'].max()

    col1, col2 = st.columns([1, 1])
    with col1:
        d1 = st.date_input("Start Date", value = df['block_timestamp'].min(), min_value=df['block_timestamp'].min(), max_value=df['block_timestamp'].max(), key = "initial_date", help=f"First txn date: {mindate}")
    with col2:
        d2 = st.date_input("End Date", value = df['block_timestamp'].max(), min_value=df['block_timestamp'].min(), max_value=df['block_timestamp'].max(), key="final_date", help=f"Last txn date: {maxdate}")
    df = df[df['block_timestamp'].between(d1, d2)].reset_index(drop=True)
    
    return df

if 'token_clicked' not in st.session_state:
    st.session_state.token_clicked = False
def token_clicked():
    st.session_state.token_clicked = True

def filtering_token3(df_plot):
    token_list = df_plot['token_name'].unique().tolist()
    default_list = []
    if 'ETH' in token_list:
        default_list.append('ETH')
    if 'USDC' in token_list:
        default_list.append('USDC')
    if 'USDT' in token_list:
        default_list.append('USDT')
    if 'WBTC' in token_list:
        default_list.append('WBTC')
    if 'POL' in token_list:
        default_list.append('POL')
    if 'USD Coin' in token_list:
        default_list.append('USD Coin')
    if 'Tether USD' in token_list:
        default_list.append('Tether USD')
    if '(PoS) Tether USD' in token_list:
        default_list.append('(PoS) Tether USD')
    
    
    filter_3 = st.pills("Search in Tokens", options = token_list, default = None, on_change=token_clicked, selection_mode="single", key="tokens")
    if filter_3 is not None:
        df_plot = df_plot[df_plot["token_name"].isin([filter_3])].reset_index(drop=True)
    else :
        st.session_state.token_clicked = False
    return df_plot

def filtering_spam1(df_plot, token):

    filter_1 = st.multiselect(
        label="Removing Spam Token transactions for better visualisations",
        options=["Only Peer to Peer", "Filter SPAM"],
        default=["Filter SPAM", "Only Peer to Peer"], key="filter_1", disabled=True
    )

    if filter_1.count('Only Peer to Peer') > 0 and filter_1.count('Filter SPAM') > 0:
        df_plot = filtering_data(df_plot, token).reset_index(drop=True)
    if filter_1.count('Incoming') > 0 and filter_1.count('Outgoing') > 0:
        df_plot = df_plot.reset_index(drop=True)
    elif filter_1.count('Incoming') > 0:
        df_plot = df_plot[df_plot['direction'] == "receive"].reset_index(drop=True)
    elif filter_1.count('Outgoing') > 0:
        df_plot = df_plot[df_plot['direction'] == "send"].reset_index(drop=True)

    return df_plot

def dataframe_on_top(df):
    df["Hash_URL"] = "https://blockscan.com/tx/" + df["hash"]

    df['value_formatted'] = pd.to_numeric(df['value_formatted']).round(4)
    df['value_formatted'] = pd.to_numeric(df['value_formatted']).round(4)
    df['value_of_txn'] = df["value_formatted"].astype(str) + " " + df["token_name"]

    df = df.drop(["hash", "value_formatted", "token_name", "summary"], axis=1, inplace=False)
    column_to_move = df.pop("Hash_URL")
    df.insert(0, "Hash_URL", column_to_move)

    # Display DataFrame with clickable links
    st.dataframe(
        df,
        column_config={
            "Hash_URL": st.column_config.LinkColumn(
                label="Hash",
                display_text="   🔗"
            ),
            "block_timestamp": st.column_config.Column(
                label="Date"
            ),
            "token_name": st.column_config.Column(
                label="Coin"
            ),
            "from_address_entity": st.column_config.Column(
                label="Sender Entity"
            ),
            "from_address": st.column_config.Column(
                label="Sender Address"
            ),
            "to_address_entity": st.column_config.Column(
                label="Receiver Entity"
            ),
            "to_address": st.column_config.Column(
                label="Receiver Address"
            ),
            "direction": st.column_config.Column(
                label="Direction"
            ),
            "value_of_txn": st.column_config.Column(
                label="Value by Txn"
            )
        },
        use_container_width=True,
        hide_index=True
    )


##############################################################################
# CHARTING AND GRAPHING
##############################################################################

def _price(df):
    if df['token_name'][0] == 'POL':
        price = 0.5
    if df['token_name'][0] == 'ETH':
        price = 3500
    if df['token_name'][0] == 'USDC':
        price = 1
    if df['token_name'][0] == 'USDT':
        price = 1
    if df['token_name'][0] == 'WBTC':
        price = 100000
    if df['token_name'][0] == 'USD Coin':
        price = 1
    if df['token_name'][0] == '(PoS) Tether USD':
        price = 1
    if df['token_name'][0] == 'Tether USD':
        price = 1 
    return price

def incoming_volume(df1, wallet):
    wallet = wallet.lower()
    price = _price(df1)
    df1 = df1.drop(["hash", "summary"], axis =1)
    df1['value_formatted'] = pd.to_numeric(df1['value_formatted']).round(4)


    df1_from = df1.groupby(['from_address', 'from_address_entity', 'token_name'] , as_index=False).agg({
        'value_formatted': 'sum'
    })
    df1_from['frequency'] = df1.groupby(['from_address', 'from_address_entity']).size().values


    df1_to = df1.groupby(['to_address', 'to_address_entity', 'token_name'] , as_index=False).agg({
        'value_formatted': 'sum'
    })
    df1_to['frequency'] = df1.groupby(['to_address', 'to_address_entity']).size().values


    total_from = df1_to.loc[df1_to['to_address'] == wallet, 'frequency'].values
    total_to = df1_from.loc[df1_from['from_address'] == wallet, 'frequency'].values



    df1_from = df1_from[df1_from['from_address']!=wallet]
    df1_to = df1_to[df1_to['to_address']!=wallet]

    df1_from['percent'] = ((df1_from['frequency']/total_from)*100).round(1)
    df1_to['percent'] = ((df1_to['frequency']/total_to)*100).round(1)

    df1_from['USD'] = df1_from['value_formatted']*price
    df1_to['USD'] = df1_to['value_formatted']*price

    df1_from = df1_from.sort_values(by='USD', ascending=False)
    df1_to = df1_to.sort_values(by='USD', ascending=False)
    df1_from.reset_index(drop=True, inplace=True)
    df1_to.reset_index(drop=True, inplace=True)
    return df1_from

def outgoing_volume(df1, wallet):
    wallet = wallet.lower()
    price = _price(df1)

    df1 = df1.drop(["hash", "summary"], axis=1)
    df1['value_formatted'] = pd.to_numeric(df1['value_formatted']).round(4)

    df1_from = df1.groupby(['from_address', 'from_address_entity', 'token_name'], as_index=False).agg({
        'value_formatted': 'sum'
    })
    df1_from['frequency'] = df1.groupby(['from_address', 'from_address_entity']).size().values

    df1_to = df1.groupby(['to_address', 'to_address_entity', 'token_name'], as_index=False).agg({
        'value_formatted': 'sum'
    })
    df1_to['frequency'] = df1.groupby(['to_address', 'to_address_entity']).size().values

    total_from = df1_to.loc[df1_to['to_address'] == wallet, 'frequency'].values
    total_to = df1_from.loc[df1_from['from_address'] == wallet, 'frequency'].values

    df1_from = df1_from[df1_from['from_address'] != wallet]
    df1_to = df1_to[df1_to['to_address'] != wallet]

    df1_from['percent'] = ((df1_from['frequency'] / total_from) * 100).round(1)
    df1_to['percent'] = ((df1_to['frequency'] / total_to) * 100).round(1)

    df1_from['USD'] = df1_from['value_formatted'] * price
    df1_to['USD'] = df1_to['value_formatted'] * price

    df1_from = df1_from.sort_values(by='USD', ascending=False)
    df1_to = df1_to.sort_values(by='USD', ascending=False)
    df1_from.reset_index(drop=True, inplace=True)
    df1_to.reset_index(drop=True, inplace=True)
    return df1_to

def pro_graphing(df1):

    df2_from_to = df1.groupby(['from_address', 'from_address_entity', 'to_address', 'to_address_entity', 'direction'], as_index=False).agg({
        'value_formatted': 'sum'
    })
    df2_from_to['frequency'] = df1.groupby(['from_address', 'from_address_entity', 'to_address', 'to_address_entity', 'direction']).size().values

    # dictionary making
    from_address_entity_count_dict = defaultdict(lambda: {"entity": None, "sent": 0})
    for _, row in df1.iterrows():
        key = row['from_address']
        entity = row['from_address_entity']
        from_address_entity_count_dict[key]["entity"] = entity
        from_address_entity_count_dict[key]["sent"] += 1
    from_address_entity_count_dict = dict(from_address_entity_count_dict)

    to_address_entity_count_dict = defaultdict(lambda: {"entity": None, "received": 0})
    for _, row in df1.iterrows():
        key = row['to_address']
        entity = row['to_address_entity']
        to_address_entity_count_dict[key]["entity"] = entity
        to_address_entity_count_dict[key]["received"] += 1
    to_address_entity_count_dict = dict(to_address_entity_count_dict)

    combined_dict = {}
    all_keys = set(from_address_entity_count_dict.keys()).union(to_address_entity_count_dict.keys())
    for key in all_keys:
        combined_dict[key] = {}
        combined_dict[key].update(from_address_entity_count_dict.get(key, {}))
        combined_dict[key].update(to_address_entity_count_dict.get(key, {}))

    # converting dict to dataframe
    df_dict = pd.DataFrame.from_dict(combined_dict, orient='index').reset_index()
    df_dict.rename(columns={'index': 'addresses'}, inplace=True)
    df_dict[['sent', 'received']] = df_dict[['sent', 'received']].fillna(0)
    df_dict[['sent', 'received']] = df_dict[['sent', 'received']].astype(int)
    df_dict['total'] = df_dict['sent']+df_dict['received']
    total_txn = df_dict['total'].max()
    df_dict['percent'] = (df_dict['total']/total_txn)*100
    df_dict['percent'] = df_dict['percent'].round().astype(int)
    df_dict = df_dict.sort_values(by='total', ascending=False).reset_index(drop=True)

    df_format = df2_from_to.copy()
    df_format['from_percent'] = df_format['from_address'].map(dict(zip(df_dict['addresses'], df_dict['percent'])))
    df_format['to_percent'] = df_format['to_address'].map(dict(zip(df_dict['addresses'], df_dict['percent'])))


    return df_format


def all_list_making(df1):

    # dictionary making
    from_address_entity_count_dict = defaultdict(lambda: {"entity": None, "sent": 0})
    for _, row in df1.iterrows():
        key = row['from_address']
        entity = row['from_address_entity']
        from_address_entity_count_dict[key]["entity"] = entity
        from_address_entity_count_dict[key]["sent"] += 1
    from_address_entity_count_dict = dict(from_address_entity_count_dict)

    to_address_entity_count_dict = defaultdict(lambda: {"entity": None, "received": 0})
    for _, row in df1.iterrows():
        key = row['to_address']
        entity = row['to_address_entity']
        to_address_entity_count_dict[key]["entity"] = entity
        to_address_entity_count_dict[key]["received"] += 1
    to_address_entity_count_dict = dict(to_address_entity_count_dict)

    combined_dict = {}
    all_keys = set(from_address_entity_count_dict.keys()).union(to_address_entity_count_dict.keys())
    for key in all_keys:
        combined_dict[key] = {}
        combined_dict[key].update(from_address_entity_count_dict.get(key, {}))
        combined_dict[key].update(to_address_entity_count_dict.get(key, {}))

    # converting dict to dataframe
    df_dict = pd.DataFrame.from_dict(combined_dict, orient='index').reset_index()
    df_dict.rename(columns={'index': 'addresses'}, inplace=True)
    df_dict[['sent', 'received']] = df_dict[['sent', 'received']].fillna(0)
    df_dict[['sent', 'received']] = df_dict[['sent', 'received']].astype(int)
    df_dict['total'] = df_dict['sent']+df_dict['received']
    total_txn = df_dict['total'].max()
    df_dict['percent'] = (df_dict['total']/total_txn)*100
    df_dict['percent'] = df_dict['percent'].round().astype(int)
    df_dict = df_dict.sort_values(by='total', ascending=False).reset_index(drop=True)

    return df_dict

##############################################################################
# EXPORTING
##############################################################################




if st.session_state.clicked:

    if chain == "Ethereum":
        token = "ETH"
    elif chain == "Polygon":
        token = "POL"

    # querying from api
    df = api_query(length_data, wallet, chain, api_key)
    st.success('Data fetched successfully!')

    st.divider()

    df_org = df.copy()

    
    with st.sidebar:
        # st.image("/Users/aritra/Documents/WebApp/app_logo.png")
        st.title("Filtering Options")
        df = filtering_spam1(df, token)
        # df = filtering_token3(df) --------- token selection is when volume analysis
        df = filtering_date2(df, df_org)

    
    st.title("Live Filtering...")


    with st.expander("Click to load raw data..."):
        st.dataframe(df_org)
    with st.expander("Click to load filtered data...", expanded=True):
            df_showindataframe = df.copy()
            dataframe_on_top(df_showindataframe)



    st.title("Analysis Dashboard 💹")

    tab1, tab2, tab3, tab4 = st.tabs(["Most Frequent 🔄", "Compare 🆚", "Volume Analysis ⏳", "Graphical Analysis 📊"])

    with tab1:
        address_frequency = pd.concat([df['from_address'], df['to_address']]).value_counts()
        address_frequency_df = address_frequency.reset_index()
        address_frequency_df.columns = ['Linked_Addresses', 'Frequency']

        # Step 3: Map entities to addresses from both 'from_address' and 'to_address'
        from_address_entity_df = df[['from_address', 'from_address_entity']].rename(
            columns={'from_address': 'Linked_Addresses', 'from_address_entity': 'Entity'}
        )
        to_address_entity_df = df[['to_address', 'to_address_entity']].rename(
            columns={'to_address': 'Linked_Addresses', 'to_address_entity': 'Entity'}
        )

        combined_entity_df = pd.concat([from_address_entity_df, to_address_entity_df]).drop_duplicates()

        address_frequency_with_entity = pd.merge(
            address_frequency_df, combined_entity_df, on='Linked_Addresses', how='left'
        )
        total = address_frequency_with_entity[address_frequency_with_entity['Linked_Addresses'] == wallet]['Frequency'].iloc[0]
        address_frequency_with_entity = address_frequency_with_entity[address_frequency_with_entity['Linked_Addresses'] != wallet]
        address_frequency_with_entity = address_frequency_with_entity.sort_values(by='Frequency', ascending=False).reset_index(drop=True)

        address_frequency_with_entity['Percentage'] = ((address_frequency_with_entity['Frequency'] / total) * 100)
        wallet_most = address_frequency_with_entity['Linked_Addresses'].iloc[0] 

        st.dataframe(
            address_frequency_with_entity,
            column_config={
                "Linked_Addresses":st.column_config.Column(
                    "Linked Addresses",
                    help=f"Interlinked addresses with : {wallet}",
                    width=250
                ),
                "Frequency": st.column_config.Column(
                    "Frequency",
                    help="The number of times interacted",
                    width=10
                ),
                "Entity": st.column_config.Column(
                    "Entity",
                    help="Interacting Entities",
                    width=10
                ),
                "Percentage": st.column_config.ProgressColumn(
                    "％ of times interacted",
                    help="The sales volume in USD",
                    format="%.2f%%",
                    min_value=0,
                    max_value=100,
                    width=150,
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

    with tab2:
        st.header("🆚 Comparison Dashboard")

        with st.form('compare'):        
            col1, col2 = st.columns([1, 1])
            with col1:
                wallet1 = str(st.text_input("First Address:", placeholder=f"{wallet}", key="first"))    
            with col2:
                wallet2 = str(st.text_input("Second Address:", placeholder=f"{wallet_most}", key="second"))

            compare_submit = st.form_submit_button('Compare ⏳', help = "Two addresses must be on the same network", type="primary", use_container_width=True)

        if(compare_submit):
            df1 = api_query(length_data, wallet1, chain, api_key)
            df2 = api_query(length_data, wallet2, chain, api_key)
            st.success("🚀 Done Fetching!")

            col1, col2 = st.columns([1,1])
            with col1:
                df1['date'] = pd.to_datetime(df1['block_timestamp']).dt.date
                transactions_by_date = df1.groupby(['date', 'direction']).size().unstack(fill_value=0)
                plt.figure(figsize=(12, 8))
                transactions_by_date.plot(kind='bar', stacked=True, figsize=(12, 8),
                                        color=['darkseagreen', 'green'], title='Transactions Count by Date')
                plt.xlabel('Date')
                plt.ylabel('Transaction Count')
                plt.xticks(rotation=45, ha='right', fontsize=6)
                plt.legend(title='Transaction Type', labels=['Sent', 'Received'])
                plt.tight_layout()
                st.pyplot(plt)

            with col2:
                df2['date'] = pd.to_datetime(df2['block_timestamp']).dt.date
                transactions_by_date = df2.groupby(['date', 'direction']).size().unstack(fill_value=0)

                # Plot the data
                plt.figure(figsize=(12, 8))
                transactions_by_date.plot(kind='bar', stacked=True, figsize=(12, 8),
                                        color=['lightsteelblue', 'royalblue'], title='Transactions Count by Date')
                plt.xlabel('Date')
                plt.ylabel('Transaction Count')
                plt.xticks(rotation=45, ha='right', fontsize=7.5)
                plt.legend(title='Transaction Type', labels=['Sent', 'Received'])
                plt.tight_layout()
                st.pyplot(plt)

    with tab3:
        with st.sidebar:
            df = filtering_token3(df)

        if st.session_state.token_clicked == True:
            try :
                df_tab3 = df.copy()
                from_vol_df = incoming_volume(df_tab3, wallet)
                to_vol_df = outgoing_volume(df_tab3, wallet)
                
            

                st.title(f"📊 Incoming & Outgoing Volume Analysis for {df['token_name'][0]}", help='This section shows the incoming volume analysis of the wallet address')
                
                items_list = from_vol_df.columns.tolist()
                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

                with col1:
                    names = st.selectbox("Names : ", options=items_list, index = 1, key = "col1_names")
                    values = st.selectbox("Values : ", options=items_list, index = 6, key = "col1_values")
                    fig = px.pie(from_vol_df, names=names, values=values, title=f"Incoming Vol : {from_vol_df['USD'].sum().round(1)}$",
                                labels={'from_address_entity':'From', 'USD':'Value in USD'},
                                width=400,
                                height=400,
                                color_discrete_sequence=px.colors.qualitative.Pastel2)
                    st.plotly_chart(fig)
                with col2:
                    names = st.selectbox("Names : ", options=items_list, index = 1, key="col2_names")
                    values = st.selectbox("Values : ", options=items_list,index = 5, key="col2_values")
                    fig = px.pie(from_vol_df, names=names, values=values, title=f"Incoming Transactions : {from_vol_df['frequency'].sum()}",
                                labels={'from_address_entity':'From', 'frequency':'Count'},
                                width=400,
                                height=400,
                                color_discrete_sequence=px.colors.qualitative.Pastel2)
                    st.plotly_chart(fig)


                items_list_to = to_vol_df.columns.tolist()
                col1, col2 = st.columns([1, 1])

                with col3:
                    names = st.selectbox("Names : ", options=items_list_to, index = 1, key = "col1_names_to")
                    values = st.selectbox("Values : ", options=items_list_to, index = 6, key = "col1_values_to")
                    fig = px.pie(to_vol_df, names=names, values=values, title=f"Outgoing Vol : {to_vol_df['USD'].sum().round(1)}$",
                                labels={'to_address_entity':'To', 'USD':'Value in $'},
                                width=400,
                                height=400,
                                color_discrete_sequence=px.colors.qualitative.Dark24)
                    st.plotly_chart(fig)
                with col4:
                    names = st.selectbox("Names : ", options=items_list_to, index = 1, key="col2_names_to")
                    values = st.selectbox("Values : ", options=items_list_to,index = 5, key="col2_values_to")
                    fig = px.pie(to_vol_df, names=names, values=values, title=f"Outgoing Transactions : {to_vol_df['frequency'].sum()}",
                                labels={'to_address_entity':'To', 'frequency':'Count'},
                                width=400,
                                height=400,
                                color_discrete_sequence=px.colors.qualitative.Dark24)
                    st.plotly_chart(fig)
            except Exception as e:
                st.warning("Can't get price data for the token ⚠️")
        else : 
            st.warning("Select Token from the sidebar to view the volume analysis ⚠️")

    with tab4:
        df_tab4 = df.copy()
        
        top100 = st.toggle("Top 100 Rows only", True)
        if top100:
            df_tab4 = df_tab4.head(100)
        else :
            df_tab4 = df_tab4

        # df_tab4 = df_tab4.drop(['hash', 'summary'], axis=1)
        df_tab4['value_formatted'] = pd.to_numeric(df_tab4['value_formatted'], errors='coerce')
        df_tab4['value_formatted'] = df_tab4['value_formatted'].round(4)

        with st.expander("Data Customisation"):
            df_tab4 = dataframe_explorer(df_tab4, case=False)
            st.dataframe(df_tab4, use_container_width=True, hide_index = True)
        
        nodes = {}
        edges = []
        for _, row in df_tab4.iterrows():
            if row['from_address'] not in nodes:
                nodes[row['from_address']] = Node(
                    id=row['from_address'],
                    label=row['from_address_entity'],
                    color="green" if row['from_address_entity'] != "Unknown" else "gray"  # Conditional color
                )

            if row['to_address'] not in nodes:
                nodes[row['to_address']] = Node(
                    id=row['to_address'],
                    label=row['to_address_entity'],
                    color="green" if row['to_address_entity'] != "Unknown" else "gray"  # Conditional color
                )

            edges.append(
                Edge(
                    source=row['from_address'],
                    target=row['to_address'],
                    label=row['direction'].capitalize(),
                    physics=True,
                    smooth=True,
                    length=500 if (row['from_address_entity'] != "Unknown" or row['to_address_entity'] != "Unknown") else 300
                )
            )


        config = Config(
            width=1920,
            height=1080,
            directed=True,
            physics=True,  
            collapsible=True,
            hierarchical=False, 
            nodeSpacing=300, 
            stabilize = True,
            edgeMinimization=False,  
            levelSeparation=200
        )

        agraph(nodes=list(nodes.values()), edges=edges, config=config)


##############################################################################
# CREATING NEO4J DATABASE WITH STREAMLIT
##############################################################################



# st.title("Advanced Analytics",help = "We are going to do advanced analytics on the data using NEO4j Graph Method", anchor = False)

# with st.form("NEO4J"):
#     NEO4J_URI = str(st.text_input("NEO4J URI", help="Enter the URI of the NEO4J Database"))
#     NEO4J_USERNAME = str(st.text_input("NEO4J Username", help="Enter the Username of the NEO4J Database"))
#     NEO4J_PASSWORD = str(st.text_input("NEO4J Password", type="password", help="Enter the Password of the NEO4J Database"))
#     submitted_neo = st.form_submit_button("Connect to NEO4J", use_container_width=True,type="primary")

# if submitted_neo:
#     df['value_formatted'] = pd.to_numeric(df['value_formatted']).round(4)
#     st.dataframe(df)


#     web = pickle.dumps(df)

#     st.download_button(
#         label="original dataframe",
#         data=web,
#         file_name="web.pkl",
#         mime="application/octet-stream",
#         use_container_width=True,
#         key='original'
#     )


#     driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))



##############################################################################
# QUERYING NEO4J DATABASE
##############################################################################























































