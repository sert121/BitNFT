from __future__ import print_function
import time
import requests
import re
import streamlit as st
import pandas as pd
import numpy as np
import pandas as pd
import docx2txt
import hashlib
import binascii
from merkletools import MerkleTools
import SessionState
import math
import pickle
import base64
import os
import json
import uuid
import datetime
import matplotlib.pyplot as plt
import sendgrid
import os





def is_public_key(hex_data):
    if re.match('^m|n', hex_data):
        address_formats['mn'] += 1
    elif re.match('^tb1', hex_data):
        address_formats['tb1'] += 1
    elif re.match('^2', hex_data):
        address_formats['2'] += 1
    elif re.match('^tpub', hex_data):
        address_formats['tpub'] += 1
    else:
        address_formats['other']+=1
        print(hex_data)


def print_type(key):
    if key == 'tb1':
        st.markdown(f'#### SegWit : ```{value}```')
    if key == 'mn':
        st.markdown(f'####  Pubkey hash: ```{value}```')
    if key == '2':
        st.markdown(f'####  Script hash: ```{value}``` ')
    if key == 'tpub':
        st.markdown(f'####  BIP32 pubkey: ```{value}```')


class RPCHost(object):
    def __init__(self, url):
        self._session = requests.Session()
        self._url = url
        self._headers = {'content-type': 'application/json'}

    def call(self, rpcMethod, *params):
        payload = json.dumps(
            {"method": rpcMethod, "params": list(params), "jsonrpc": "2.0"})
        tries = 5
        hadConnectionFailures = False
        while True:
            try:
                response = self._session.post(
                    self._url, headers=self._headers, data=payload)
            except requests.exceptions.ConnectionError:
                tries -= 1
                if tries == 0:
                    raise Exception(
                        'Failed to connect for remote procedure call.')
                hadFailedConnections = True
                print("Couldn't connect for remote procedure call, will sleep for five seconds and then try again ({} more tries)".format(tries))
                time.sleep(10)
            else:
                if hadConnectionFailures:
                    print('Connected for remote procedure call after retry.')
                break
        if not response.status_code in (200, 500):
            raise Exception('RPC connection failure: ' +
                            str(response.status_code) + ' ' + response.reason)
        responseJSON = response.json()
        if 'error' in responseJSON and responseJSON['error'] != None:
            # raise Exception('Error in RPC call: ' + str(responseJSON['error']))
            if (rpcMethod == 'getrawtransaction'):
                st.error('Error in transaction id. Please provide the correct details')
                st.stop()
            else:
                st.error("Some error has occured, please retry")
                st.stop()
                # raise Exception('Error in RPC call: ' + str(responseJSON['error']))
                # print('Error in RPC call: ' + str(responseJSON['error']))
            st.stop()
        return responseJSON['result']

# Default port for the bitcoin testnet is 18332
# The port number depends on the one writtein the bitcoin.conf file
rpcPort = 18332
# The RPC username and RPC password MUST match the one in your bitcoin.conf file
rpcUser = 'bitcoin'
rpcPassword = 'kuchbhidaalo'
# Accessing the RPC local server
serverURL = 'http://' + rpcUser + ':' + \
    rpcPassword + '@127.0.0.1:18332'
# Using the class defined in the bitcoin_rpc_class.py
host = RPCHost(serverURL)




col1,col2 = st.beta_columns(2)

with st.beta_container():
    st.markdown("<h1 style='text-align: center; color: white;'>BitExplorer</h1>",
            unsafe_allow_html=True)


# regex for valid block or transaction hash
hash_pattern = '^[a-fA-F0-9]{64}$'
block_pattern = '^[0]{8}[a-fA-F0-9]{56}$'

st.markdown("<br></br>",unsafe_allow_html=True)
st.write("1. Enter hash to check if a hex is likely to be a transaction or a block")
st.code('''Expected input: hex string (e.g: a4b6e345677c3de)
Expected output: It's likely a block/transaction OR Invalid''',language="bash")
hash_input = st.text_input('Enter hash', '')

if hash_input!='':
    result = re.match(hash_pattern, hash_input)
    result2 = re.match(block_pattern, hash_input)
    if result and result2:
        st.info("most likely a valid block")
    elif result and not result2:
        st.info("most likely a valid transaction")
    else:
        st.info("Invalid hash")

st.markdown("---")

# st.write("https://google.com")
# link = '[GitHub](http://github.com)'
# st.markdown(link, unsafe_allow_html=True)
# with st.button("Click here",):
#     st.markdown(link, unsafe_allow_html=True)

st.write("2. Compute specific block/txn details")
option1 = st.selectbox("",["Search via block height","Search via transaction id"])

if option1 =="Search via block height":
    st.code('''Expected input: Block height (int)''',language="bash")
    address_formats = {'mn': 0, 'tb1': 0, '2': 0, 'tpub': 0,'other':0}
    block_no=''
    block=''
    block_existence=False
    total_tx = 0
    block_no=st.number_input('Enter block height', max_value=host.call('getblockcount'))
    segwit_no = 0
    if block_no != '' and block_no != 0:
        block_hash=host.call("getblockhash", int(block_no)
                            )  # recieves hex string
        block=host.call("getblock", block_hash, 2)  # 2 for verbosity
        if block != '':
            block_existence = True
        
        block_transactions=block['tx']
        total_tx = len(block_transactions)
        # not considering coinbase
        block_transactions=block_transactions[1:]
        for t in block_transactions:
            outputs=t["vout"]
            for j in outputs:
                if j["scriptPubKey"].get('addresses'):
                    addresses=j["scriptPubKey"]['addresses']
                    for addr in addresses:
                        is_public_key(addr)
            inputs = t["vin"]
            for j in inputs:
                txxid = j["txid"]
                seg = host.call('getrawtransaction', txxid)
                if seg[8:10]=='00':
                    segwit_no+=1
                    break

    col1,col2 = st.beta_columns(2)
    with col1:
        col1.subheader("Transactions")
        st.code('''Expected output: Number of Total transactions, categorized as regular and sewgit. ''',language="bash")
        st.markdown(f"#### No. of Total transactions: ```{total_tx}```")
        st.markdown(f"#### No. of Regular transactions: ```{total_tx - segwit_no}```")
        st.markdown(f"####  No. of Segwit transactions: ```{segwit_no}```")
        st.markdown('<br>',unsafe_allow_html=True)
        s = '[Read More](https://bitcoin.stackexchange.com/questions/66571/what-is-the-difference-between-segwit-and-non-segwit)'
        st.markdown(s, unsafe_allow_html=True)
    with col2:
        col2.subheader("Address Types")
        st.code('''Expected output: Count of specified address types in a particular block''',language="bash")
        for key, value in address_formats.items():
            print_type(key)
        st.markdown("<br>",unsafe_allow_html=True)
        link = '[Read More](https://en.bitcoin.it/wiki/List_of_address_prefixes)'
        st.markdown(link, unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)    
    st.subheader("Block Details")
    st.code('''Displays Json formatted output of the block ''',language='javascript')
    if block_existence:
        st.write(block)

else:
    search_query=st.text_input('Enter transaction id to search', '')
    segwit_no = 0
    st.code('''Expected input: Transaction id (hex string)''',language="javascript")
    if search_query != '':
        
        transactionHex=host.call('getrawtransaction', search_query)
        # if transactionHex[8:10] == '00':
        #     st.write("This is a SegWit transaction")
        transaction=host.call('decoderawtransaction', transactionHex)
        valid_txn = False
        inputs=transaction["vin"]


        for j in inputs:
            try:
                txxid = j["txid"]
                valid_txn = True
            except:
                st.error("Incompatible transaction Type. Maybe Coinbase")
                continue
            seg = host.call('getrawtransaction', txxid)
            if seg[8:10] == '00':
                segwit_no += 1
        # st.write(f"No. of segWit inputs:{segwit_no}")
        outputs=transaction["vout"]

        st.text('\n')

        # st.markdown('''Details required:''')
        # bool1=st.checkbox('Address Format')
        bool1=True        


        pub_formats={}

        for j in outputs:
            if j["scriptPubKey"].get('addresses'):
                addresses=j["scriptPubKey"]['addresses']
                for addr in addresses:
                    address_formats = {'mn': 0, 'tb1': 0, '2': 0, 'tpub': 0, 'other': 0}
                    is_public_key(addr)
                    for key,value in address_formats.items():
                        if address_formats[key]==1:
                            break
                    pub_formats[addr]=key
            
#             # else:
        
        if(len(pub_formats) > 0):
            pass
        else:
           st.error("No addresses found!")
           bool1=False


        map_addr = {'mn': 'Pubkey hash', 'tb1': 'SegWit (P2WPKH/P2WSH address)', '2': 'Script hash', 'tpub': 'BIP32'}
        
        if bool1 == True:
            st.subheader("Addresses")
            # st.code('''Expected output: Block height (int)''',language="python")
            st.code("Displays wallet addresses which are a part of the transaction ")
            for key, val in pub_formats.items():
                st.markdown(f" ```{key}``` ({map_addr[str(val)]})")
                # print_type(val)
        st.subheader("Transaction Details")
        st.write(transaction)
        # if(len(pub_formats) > 0):
        #     print("Addresses Found")
        # else:
        #     st.error("No addresses found!")
        
st.markdown("---")
st.write("3. Compute details of a range of blocks")
block_range_flag = st.selectbox("Enter Block range",["via Date","via Block Height "])
n=100000
H1, H2 = 0, 0
if block_range_flag=="via Date":
    col1,col2 = st.beta_columns(2)
    first_b = datetime.date(2009, 1, 3)
    with col1:
        date1 = st.date_input("Starting Date")
    with col2:
        date2 = st.date_input("Ending Date")

    diff = date2 - date1
    diff = diff.total_seconds()//600
    blocks_passed = date1 - first_b
    blocks_passed = blocks_passed.total_seconds()//600
    H1 = blocks_passed
    H2 = blocks_passed + diff


else:
    col1, col2 = st.beta_columns(2)
    with col1:
        H1 = st.number_input("start", min_value=1,
                             max_value=host.call('getblockcount'))
    with col2:
        H2 = st.number_input("end", min_value=1,
                             max_value=host.call('getblockcount'))


H1,H2 = int(H1),int(H2)
op_counter=0
multisig_counter=0
ophash_counter=0
segwit_transaction=0
address_formats = {'mn': 0, 'tb1': 0, '2': 0, 'tpub': 0, 'other': 0}
tag=0
total_tx = 0
with st.spinner('Wait for it...'):
    for i in range(H1,H2):
        block_hash = host.call("getblockhash", i)
        block = host.call("getblock", block_hash, 2)  # 2 for verbosity
        block_transactions = block['tx']
        total_tx += len(block_transactions)
        block_transactions = block_transactions[1:]
        for t in block_transactions:
            outputs = t["vout"]
            for j in outputs:
                if j["scriptPubKey"].get('addresses'):
                    addresses = j["scriptPubKey"]['addresses']
                    for addr in addresses:
                        is_public_key(addr)
                if j["scriptPubKey"].get('asm'):
                    asm = addresses = j["scriptPubKey"]['asm']
                    if re.match('^OP_RETURN', asm):
                        op_counter+=1
                    if re.match('^OP_CHECKMULTISIG$',asm):   #Check for dollar
                        multisig_counter+=1
                    if re.match('^OP_HASH160',asm):
                        ophash_counter+=1
            inputs = t["vin"]
            for j in inputs:
                txxid = j["txid"]
                seg = host.call('getrawtransaction', txxid)
                if seg[8:10] == '00':
                    segwit_transaction += 1
                    break
    tag=1

col1,col2,col3 = st.beta_columns(3)
with col1:
    col1.subheader("Transactions")
    st.code('''Expected output: Total number of transactions, categorized into regular & segwit txns''')
    st.markdown(f"#### Total txns: ```{total_tx}```")
    st.markdown(f"#### Regular txns: ```{total_tx - segwit_transaction}```")
    st.markdown(f"#### Segwit txns: ```{segwit_transaction}```")
    st.markdown('<br>',unsafe_allow_html=True)
    s = '[Read More](https://bitcoin.stackexchange.com/questions/66571/what-is-the-difference-between-segwit-and-non-segwit)'
    st.markdown(s, unsafe_allow_html=True)
with col2:
    col2.subheader("Address Types")
    st.code(''' Expected output:  Count of specified address types in a range of blocks ''')
    for key, value in address_formats.items():
        print_type(key)
    st.markdown("<br>",unsafe_allow_html=True)
    link = '[Read More](https://en.bitcoin.it/wiki/List_of_address_prefixes)'
    st.markdown(link, unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)    
    # st.subheader("Block Details")
    # st.code('''Displays Json formatted output of the block ''',language='javascript')
    # if block_existence:
    #     st.write(block)
with col3:
    col3.subheader("TX Outputs")
    st.code(''' Expected output: Count of transaction outputs such as OP_RETURN and OP_HASH in specified block range''',language="bash")
    st.markdown(f"####  ```OP_RETURN``` : ```{op_counter}```")
    st.markdown(f"####  ```OP_HASH``` : ```{ophash_counter}```")
    st.markdown('<br>',unsafe_allow_html=True)
    s = '[Read More](https://en.bitcoin.it/wiki/Script)'
    st.markdown(s, unsafe_allow_html=True)


# if tag==1:
#     #st.balloons()
#     st.markdown("ADDRESS FIELD:")
#     for key, value in address_formats.items():
#         print_type(key)
#     st.markdown("TRANSACTION TYPE:")
#     st.markdown(f"No. of segwit transactions: ```{segwit_transaction}```")
#     st.markdown(f"No. of opreturn transactions: ```{op_counter} ```")
#     st.markdown(f"No. of multisig transactions: ```{multisig_counter}```")
#     st.markdown(f"No. of ophash transactions: ```{ophash_counter}```")



# st.info('This is a purely informational message')


# Mention total number of transaction in the output
# Add more attributes. 
# Make the website a little more informative. 
# There are only 2 kind of transaction, segwit and regular
# Multsig, and op_return are type of output (lockscripts)
