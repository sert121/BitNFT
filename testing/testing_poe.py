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

st.set_page_config(layout="wide")


def download_button(object_to_download, download_filename, button_text, pickle_it=False):
    if pickle_it:
        try:
            object_to_download = pickle.dumps(object_to_download)
        except pickle.PicklingError as e:
            st.write(e)
            return None

    else:
        if isinstance(object_to_download, bytes):
            pass

        elif isinstance(object_to_download, pd.DataFrame):
            object_to_download = object_to_download.to_csv(index=False)

        # Try JSON encode for everything else
        else:
            object_to_download = json.dumps(object_to_download)

    try:
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download.encode()).decode()

    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()

    button_uuid = str(uuid.uuid4()).replace('-', '')
    button_id = re.sub('\d+', '', button_uuid)

    custom_css = f"""
        <style>
            # {button_id} {{
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: 0.25em 0.38em;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }}
            # {button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            # {button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    dl_link = custom_css + \
        f'<a download="{download_filename}" id="{button_id}" href="data:file/txt;base64,{b64}">{button_text}</a><br></br>'

    return dl_link


################ Globals ##############

session = SessionState.get(ra='', digest='', proof={}, uploadedProof={})
fee = 0.00001
receivedTransaction = None
prefix = "444f4350524f4f46"

################ Globals ##############
############# Bitcoin Functions #########


def sendTransaction(inputs, digest, address, amount):
    inputString = [{"txid": inputs['txid'], "vout": inputs['vout']}]
    digestString = [{"data": digest}, {address: amount}]
    rawTransaction = host.call(
        'createrawtransaction', inputString, digestString)
    signedTransaction = host.call(
        'signrawtransactionwithwallet', rawTransaction)
    sentTransaction = host.call('sendrawtransaction', signedTransaction['hex'])
    return sentTransaction


def checkForConfirmation(transaction):
    unspent = host.call('listunspent')
    for t in unspent:
        if transaction['txid'] == t['txid']:
            return t
    print("Transaction not yet confirmed")
    st.write("Transaction not yet confirmed")
    return


def poe(receiveAddress, digest):
    transactions = host.call('listtransactions')
    # Variable to check received
    received = False

    for transaction in transactions:
        if transaction['category'] == "receive":
            if (transaction['address'] == receiveAddress):
                # Money at least been sent
                print("Waiting for confirmation")
                st.write("Waiting for confirmation")
                received = True
                receivedTransaction = transaction
                break

    if not received:
        # Show error
        print("Money not received")
        st.write("Money not received")
    else:
        ticks = 0
        while True:
            tx = checkForConfirmation(receivedTransaction)
            if tx:
                # Transaction confirmed
                print("Transaction confirmed")
                st.write("Money successfully received with block confirmation")
                changeAddress = host.call('getrawchangeaddress')
                am = tx['amount'] - fee
                print(am)
                document = prefix + digest
                sentTransaction = sendTransaction(
                    tx, document, changeAddress, round(am, 7))
                st.write("TxID", sentTransaction)

                download_button_str = download_button(
                    session.proof, "docProof", f'Click here to download', pickle_it=True)
                st.markdown(download_button_str, unsafe_allow_html=True)

                print(sentTransaction)
                break
            else:
                # Transaction not confirmed. Wait for 1 min
                if ticks == 10:
                    print("Breaking the loop. 10 min passed. No money received")
                    st.write(
                        "10 min passed. No money received")
                    break
                else:
                    time.sleep(60)
                    ticks += 1
############# Bitcoin Functions #########
############# Merkle Root #########


def merkleRoot(hashDocList, docNumber):
    mt = MerkleTools()
    mt.add_leaf(hashDocList)
    mt.make_tree()
    root = mt.get_merkle_root()
    print(f"M tree root: {root}")

    documentProof = {}
    for i in range(docNumber):
        proof = mt.get_proof(i)
        documentProof[hashDocList[i]] = proof
    session.proof = documentProof
    return root, documentProof
############# Merkle Root #########

############ Connection #################################


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
            raise Exception('Error in RPC call: ' + str(responseJSON['error']))
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

# print(host.call('getblockchaininfo'))


################### Connection ###########################
################## Main Setup #############

# st.title('BitNFT')
with st.beta_container():
    st.markdown("<h1 style='text-align: center; color: white;'>BitNFT</h1>",
                unsafe_allow_html=True)
with st.beta_container():
    st.markdown("<h3 style='text-align: center; color: white;'>Info</h3>",unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: white;font:Courier New;'>Info</p>",unsafe_allow_html=True)

col1, col2 = st.beta_columns(2)
st.text("\n\n")
with col1:
    st.subheader('Prove')
    st.text("\n\n") 
    st.text('You can upload your own document, or paste it here.')

    uploaded_file = st.file_uploader(
        "Upload your file(s)", accept_multiple_files=True, type=['txt', 'docx', 'pdf'])
    if uploaded_file:
        if st.button("Process"):
            hashDoc = []
            for i in uploaded_file:
                docx_file = i
                if docx_file.type == "text/plain":
                    raw_text = docx_file.read()

                elif docx_file.type == "application/pdf":
                    raw_text = docx_file.read()

                elif docx_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    raw_text = docx2txt.process(docx_file)

                hex_string = (hashlib.sha256(raw_text)).hexdigest()
                hashDoc.append(hex_string)

            documentsNumber = len(hashDoc)
            treeLength = math.ceil(math.log(documentsNumber, 2))
            toAppend = hashDoc[-1]
            for d in range(documentsNumber, (2**treeLength)):
                hashDoc.append(toAppend)

            print(hashDoc)
            root, proofs = merkleRoot(hashDoc, documentsNumber)
            session.digest = root
            st.write("Digest", root)

            # Show address to Pay
            receiveAddress = host.call('getnewaddress')
            session.ra = receiveAddress
            st.write("Pay 0.0025 BTC at", session.ra)

    if uploaded_file != None:
        st.write("To complete the process, please pay below")
        if st.button("I have Paid. Proceed to Certify"):
            poe(session.ra, session.digest)
    ################## Main Setup #############
with col2:

    ################# Verification #################
    st.subheader("Verification")
    st.text("Provide brief description here")
    st.text('Upload your transaction id here')
    txidProof = ''
    txidProof = st.text_input('''Enter transaction id''')
    st.text('\n')

    uploaded_proof = st.file_uploader(
        "Upload your Proof", accept_multiple_files=False)

    uploadedDocumentToProve = st.file_uploader(
        "Upload your Document", accept_multiple_files=False)

    if st.button("Verify"):
        if uploaded_proof:
            upProof = pickle.loads(uploaded_proof.read())
            session.uploadedProof = upProof

        if uploadedDocumentToProve:
            if uploadedDocumentToProve.type == "text/plain":
                raw_text = uploadedDocumentToProve.read()

            elif uploadedDocumentToProve.type == "application/pdf":
                raw_text = uploadedDocumentToProve.read()

            elif uploadedDocumentToProve.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                raw_text = docx2txt.process(uploadedDocumentToProve)

            hex_string = (hashlib.sha256(raw_text)
                          ).hexdigest()   # Document Hash

        if uploaded_proof and uploadedDocumentToProve:
            st.success("All files successfully uploaded!")
        else:
            st.error(
                "Error! Not all files have been uploaded succesfully. Please re-upload")

        rawTxn = host.call("getrawtransaction", txidProof)
        decodedTxn = host.call("decoderawtransaction", rawTxn)
        root = decodedTxn["vout"][0]["scriptPubKey"]["hex"][20:]

        mt = MerkleTools()
        key = 0
        for key, val in upProof.items():  # found doc's hash
            if key == hex_string:
                break

        result = mt.validate_proof(upProof[key], hex_string, root)
        st.write(result)

    ################# Verification #################

with st.beta_container():
    st.markdown("<h1 style='text-align: center; color: white;'>Additional Explorer</h1>",
                unsafe_allow_html=True)

address_formats = {'mn': 0, 'tb1': 0, '2': 0, '9': 0, 'c': 0, 'tpub': 0,'other':0}


def is_public_key(hex_data):
    if re.match('^m|n', hex_data):
        address_formats['mn'] += 1
    if re.match('^tb1', hex_data):
        address_formats['tb1'] += 1
    if re.match('^2', hex_data):
        address_formats['2'] += 1
    if re.match('^9', hex_data):
        address_formats['9'] += 1
    if re.match('^c', hex_data):
        address_formats['c'] += 1
    if re.match('^tpub', hex_data):
        address_formats['tpub'] += 1
    else:
        address_formats['other']+=1
block_no=''
block=''
block_no=st.text_input('Enter block height', '')


if block_no != '':
    block_hash=host.call("getblockhash", int(block_no)
                           )  # recieves hex string
    block=host.call("getblock", block_hash, 2)  # 2 for verbosity
    if block != '':
        st.write(block)

    block_transactions=block['tx']
    for t in block_transactions:
        outputs=t["vout"]

        for j in outputs:
            if j["scriptPubKey"].get('addresses'):
                addresses=j["scriptPubKey"]['addresses']
                for addr in addresses:
                    is_public_key(addr)
def print_type(key):   
    if key == 'tb1': 
        st.text(f'SegWit Testnet(P2WPKH or P2WSH address):{value}')
    if key == 'mn':
        st.text(f'Testnet pubkey hash: {value}')
    if key == '2':
        st.text(f'Testnet script hash:{value}')
    if key == '9':
        st.text(f'Testnet Private key (WIF, uncompressed pubkey):{value}')
    if key == 'c':
        st.text(f'Testnet Private key (WIF, compressed pubkey):{value}')
    if key == 'tpub':
        st.text(f'Testnet BIP32 pubkey:{value}')
    if key == 'other':
        st.text(f'Other:{value}')


for key, value in address_formats.items():
    print_type(key)
search_query=st.text_input('Enter transaction id to search', '')
if search_query != '':

    transactionHex=host.call('getrawtransaction', search_query)
    transaction=host.call('decoderawtransaction', transactionHex)

    outputs=transaction["vout"]

    st.text('\n')

    st.markdown('''Details required:''')
    bool1=st.checkbox('Address Format')
    bool2=st.checkbox('Encoding Format')


    pub_formats={}

    for j in outputs:
        if j["scriptPubKey"].get('addresses'):
            addresses=j["scriptPubKey"]['addresses']
            for addr in addresses:
                address_formats = {'mn': 0, 'tb1': 0, '2': 0,
                                   '9': 0, 'c': 0, 'tpub': 0, 'other': 0}
                is_public_key(addr)
                for key,value in address_formats.items():
                    if address_formats[key]==1:
                        break
                pub_formats[addr]=key
        else:
            st.error("No addresses found!")
    
    if bool1 == True:
        col1, col2 = st.beta_columns(2)
        with col1:
            st.subheader("Address")
            for key, val in pub_formats.items():
                st.text(f"{key}")
                print_type(val)
        with col2:
            st.subheader("Encoding")
            st.write("the encoding format is:")
    elif bool2 == True:
        col1, col2 = st.beta_columns(2)
        with col1:
            st.subheader("Address")
        with col2:
            st.subheader("Encoding")
            st.write("the encoding format is:")
    elif bool1 == True and bool2 == True:
        col1, col2 = st.beta_columns(2)
        with col1:
            st.subheader("Address")
            for key, val in pub_formats.items():
                st.text(f"{key}")
                print_type(val)
        with col2:
            st.subheader("Encoding")
            st.write("the encoding format is:")
    

n=100000

# values=st.slider('Select a range of values', 1, host.call(
#     "getblockcount"), (host.call("getblockcount")//5, host.call("getblockcount")//3))
# st.write(values)
st.markdown('''Details required:''')
bool1 = st.checkbox('OP Return')
bool2 = st.checkbox('OP MULTISIG')

op_counter=0
multisig_counter=0

for i in range(1000000,1000100):
    block_hash = host.call("getblockhash", i)
    block = host.call("getblock", block_hash, 2)  # 2 for verbosity
    block_transactions = block['tx']
    for t in block_transactions:
        outputs = t["vout"]
        for j in outputs:
            if j["scriptPubKey"].get('asm'):
                asm = addresses = j["scriptPubKey"]['asm']
                if re.match('^OP_RETURN', asm):
                    op_counter+=1
                if re.search(r'OP_CHECKMULTISIG$',asm):
                    multisig_counter+=1

if bool1 == True:
    col1, col2 = st.beta_columns(2)
    with col1:
        st.subheader("OP_RETURN")
        st.text(f"No. of OP_RETURN transactions:{op_counter}")

    with col2:
        st.subheader("MULTISIG")
        st.text(f"No. of MULTISIG transactions:{multisig_counter}")


col1, col2 = st.beta_columns(2)
with col1:
    H1 = st.number_input("start",min_value=1,max_value=1000000)
with col2:
    H2 = st.number_input("end", min_value=1, max_value=1000000)

